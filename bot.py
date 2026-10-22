import base64
import json
import logging
import os
import time
import uuid

import boto3
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

logger = logging.getLogger()
logger.setLevel(logging.INFO)

PROJECT = os.environ.get("PROJECT", "game-bot")
CONFIG_BUCKET = os.environ.get("CONFIG_BUCKET", f"{PROJECT}-game-config")
DISCORD_PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY", "")
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

ECS_CLUSTER = f"{PROJECT}-cluster"
ACTIVITY_CHECK_INTERVAL = "rate(15 minutes)"

ecs = boto3.client("ecs", region_name=AWS_REGION)
s3 = boto3.client("s3", region_name=AWS_REGION)
secrets = boto3.client("secretsmanager", region_name=AWS_REGION)
events = boto3.client("events", region_name=AWS_REGION)
backup = boto3.client("backup", region_name=AWS_REGION)
sts = boto3.client("sts", region_name=AWS_REGION)


# --- Game config from S3 ---


def load_game_configs():
    configs = {}
    resp = s3.list_objects_v2(Bucket=CONFIG_BUCKET)
    for obj in resp.get("Contents", []):
        key = obj["Key"]
        if not key.endswith("/server.json"):
            continue
        data = s3.get_object(Bucket=CONFIG_BUCKET, Key=key)
        config = json.loads(data["Body"].read())
        configs[config["game"]] = config
    return configs


def get_game_config(game):
    key = f"{game}/server.json"
    data = s3.get_object(Bucket=CONFIG_BUCKET, Key=key)
    return json.loads(data["Body"].read())


def list_enabled_games():
    configs = load_game_configs()
    return {name: cfg for name, cfg in configs.items() if cfg.get("enabled")}


# --- Discord interaction handling ---


def verify_signature(event):
    body = event.get("body", "")
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")
    headers = {k.lower(): v for k, v in event.get("headers", {}).items()}
    signature = headers.get("x-signature-ed25519", "")
    timestamp = headers.get("x-signature-timestamp", "")

    verify_key = VerifyKey(bytes.fromhex(DISCORD_PUBLIC_KEY))
    verify_key.verify(f"{timestamp}{body}".encode(), bytes.fromhex(signature))
    return body


def discord_response(content, ephemeral=False):
    data = {"content": content}
    if ephemeral:
        data["flags"] = 64
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"type": 4, "data": data}),
    }


def handler(event, context):
    try:
        raw_body = verify_signature(event)
    except (BadSignatureError, Exception):
        return {"statusCode": 401, "body": "Invalid request signature"}

    body = json.loads(raw_body)

    if body.get("type") == 1:
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"type": 1}),
        }

    if body.get("type") == 2:
        return handle_command(body)

    return {"statusCode": 400, "body": "Unknown interaction type"}


def handle_command(body):
    command = body["data"]["name"]
    options = {
        opt["name"]: opt["value"] for opt in body["data"].get("options", [])
    }

    commands = {
        "start": cmd_start,
        "stop": cmd_stop,
        "status": cmd_status,
    }

    fn = commands.get(command)
    if not fn:
        return discord_response(f"Unknown command: {command}")

    try:
        return fn(options)
    except Exception:
        logger.exception("Command %s failed", command)
        return discord_response("Something went wrong. Check the logs.", ephemeral=True)


# --- Commands ---


def cmd_start(options):
    game = options.get("game", "").lower()

    try:
        config = get_game_config(game)
    except s3.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchKey":
            enabled = list_enabled_games()
            available = ", ".join(enabled.keys())
            return discord_response(f"Unknown game. Available: {available}")
        raise

    if not config.get("enabled"):
        return discord_response(f"**{game}** is not enabled yet.")

    running = get_running_task()
    if running:
        return discord_response(
            f"A server is already running (task `{running['taskArn'].split('/')[-1]}`). "
            "Stop it first with `/stop`."
        )

    token = generate_server_token(game)
    task_arn = start_ecs_task(config, token)
    create_activity_cron(game, task_arn)
    task_id = task_arn.split("/")[-1]

    return discord_response(
        f"**{game}** server is starting up!\n"
        f"Task: `{task_id}`\n"
        f"Join token: ||{token}||\n"
        "It may take a few minutes to be reachable."
    )


def cmd_stop(options):
    running = get_running_task()
    if not running:
        return discord_response("No server is currently running.")

    task_arn = running["taskArn"]
    task_id = task_arn.split("/")[-1]
    game = extract_game_from_task(running)

    start_backup(game)
    delete_activity_cron(game)
    delete_server_token(game)

    ecs.stop_task(cluster=ECS_CLUSTER, task=task_arn, reason="Stopped via Discord bot")

    return discord_response(
        f"**{game}** server is shutting down.\n"
        f"Task `{task_id}` stopped. Backup started."
    )


def cmd_status(options):
    running = get_running_task()
    if not running:
        return discord_response("No server is currently running.")

    task_arn = running["taskArn"]
    task_id = task_arn.split("/")[-1]
    game = extract_game_from_task(running)
    status = running.get("lastStatus", "UNKNOWN")
    started = running.get("startedAt")

    uptime = ""
    if started:
        delta = int(time.time() - started.timestamp())
        hours, remainder = divmod(delta, 3600)
        minutes, _ = divmod(remainder, 60)
        uptime = f"\nUptime: {hours}h {minutes}m"

    return discord_response(
        f"**{game}** — `{status}`\nTask: `{task_id}`{uptime}"
    )


# --- ECS ---


def get_running_task():
    resp = ecs.list_tasks(cluster=ECS_CLUSTER, desiredStatus="RUNNING")
    task_arns = resp.get("taskArns", [])
    if not task_arns:
        return None

    desc = ecs.describe_tasks(cluster=ECS_CLUSTER, tasks=[task_arns[0]])
    tasks = desc.get("tasks", [])
    return tasks[0] if tasks else None


def start_ecs_task(config, token):
    env = [{"name": k, "value": v} for k, v in config.get("env_defaults", {}).items()]
    env.append({"name": "SERVER_PASS", "value": token})

    resp = ecs.run_task(
        cluster=ECS_CLUSTER,
        taskDefinition=config["task_definition"],
        launchType="FARGATE",
        count=1,
        networkConfiguration={
            "awsvpcConfiguration": {
                "assignPublicIp": "ENABLED",
                "subnets": get_public_subnets(),
                "securityGroups": get_security_groups(),
            }
        },
        overrides={
            "containerOverrides": [
                {
                    "name": config["container_name"],
                    "environment": env,
                }
            ]
        },
    )

    task = resp["tasks"][0]
    return task["taskArn"]


def extract_game_from_task(task):
    td = task.get("taskDefinitionArn", "")
    try:
        configs = load_game_configs()
        for game, config in configs.items():
            if config["task_definition"] in td:
                return game
    except Exception:
        logger.exception("Failed to load game configs for task extraction")
    return "unknown"


def get_public_subnets():
    ec2 = boto3.client("ec2", region_name=AWS_REGION)
    resp = ec2.describe_subnets(
        Filters=[
            {"Name": "tag:Name", "Values": [f"{PROJECT}-public-*"]},
        ]
    )
    return [s["SubnetId"] for s in resp["Subnets"]]


def get_security_groups():
    ec2 = boto3.client("ec2", region_name=AWS_REGION)
    resp = ec2.describe_security_groups(
        Filters=[
            {"Name": "tag:Name", "Values": [f"{PROJECT}-ecs-tasks"]},
        ]
    )
    return [sg["GroupId"] for sg in resp["SecurityGroups"]]


# --- Secrets Manager ---


def generate_server_token(game):
    token = uuid.uuid4().hex[:12]
    secret_name = f"{PROJECT}/{game}/server-token"

    try:
        secrets.create_secret(Name=secret_name, SecretString=token)
    except secrets.exceptions.ResourceExistsException:
        secrets.put_secret_value(SecretId=secret_name, SecretString=token)

    return token


def delete_server_token(game):
    secret_name = f"{PROJECT}/{game}/server-token"
    try:
        secrets.delete_secret(
            SecretId=secret_name, ForceDeleteWithoutRecovery=True
        )
    except secrets.exceptions.ResourceNotFoundException:
        pass


# --- EventBridge ---


def create_activity_cron(game, task_arn):
    rule_name = f"{PROJECT}-{game}-activity-check"

    events.put_rule(
        Name=rule_name,
        ScheduleExpression=ACTIVITY_CHECK_INTERVAL,
        State="ENABLED",
        Description=f"Activity check for {game} server",
    )

    account_id = sts.get_caller_identity()["Account"]
    events.put_targets(
        Rule=rule_name,
        Targets=[
            {
                "Id": f"{game}-activity-target",
                "Arn": f"arn:aws:lambda:{AWS_REGION}:{account_id}:function:{PROJECT}-discord-bot",
                "Input": json.dumps(
                    {"source": "activity-check", "game": game, "task_arn": task_arn}
                ),
            }
        ],
    )


def delete_activity_cron(game):
    rule_name = f"{PROJECT}-{game}-activity-check"

    try:
        events.remove_targets(Rule=rule_name, Ids=[f"{game}-activity-target"])
    except events.exceptions.ResourceNotFoundException:
        pass

    try:
        events.delete_rule(Name=rule_name)
    except events.exceptions.ResourceNotFoundException:
        pass


# --- Backup ---


def start_backup(game):
    account_id = sts.get_caller_identity()["Account"]
    try:
        backup.start_backup_job(
            BackupVaultName=f"{PROJECT}-game-data",
            ResourceArn=f"arn:aws:elasticfilesystem:{AWS_REGION}:{account_id}:file-system/{get_efs_id()}",
            IamRoleArn=f"arn:aws:iam::{account_id}:role/{PROJECT}-backup-role",
        )
    except Exception:
        logger.exception("Failed to start backup for %s", game)


def get_efs_id():
    efs = boto3.client("efs", region_name=AWS_REGION)
    resp = efs.describe_file_systems()
    for fs in resp["FileSystems"]:
        for tag in fs.get("Tags", []):
            if tag["Key"] == "Name" and tag["Value"] == f"{PROJECT}-game-data":
                return fs["FileSystemId"]
    return None
