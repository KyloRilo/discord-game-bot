import json
import os
import sys
from glob import glob
from urllib.request import Request, urlopen

DISCORD_API = "https://discord.com/api/v10"


def load_game_choices():
    choices = []
    for path in sorted(glob("build/*/server.json")):
        with open(path) as f:
            config = json.load(f)
        if config.get("enabled"):
            choices.append({"name": config["game"].capitalize(), "value": config["game"]})
    return choices


def inject_choices(commands, choices):
    for cmd in commands:
        if cmd["name"] != "start":
            continue
        for opt in cmd.get("options", []):
            if opt["name"] == "game":
                opt["choices"] = choices
    return commands


def register(app_id, bot_token, commands):
    url = f"{DISCORD_API}/applications/{app_id}/commands"
    data = json.dumps(commands).encode()
    req = Request(url, data=data, method="PUT", headers={
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json",
    })
    with urlopen(req) as resp:
        body = json.loads(resp.read())
    return body


def main():
    app_id = os.environ.get("DISCORD_APPLICATION_ID")
    bot_token = os.environ.get("DISCORD_BOT_TOKEN")
    if not app_id or not bot_token:
        print("DISCORD_APPLICATION_ID and DISCORD_BOT_TOKEN must be set")
        sys.exit(1)

    with open("commands.json") as f:
        commands = json.load(f)

    choices = load_game_choices()
    if not choices:
        print("No enabled games found in build/*/server.json")
        sys.exit(1)

    commands = inject_choices(commands, choices)

    print(f"Registering {len(commands)} commands with game choices: {[c['value'] for c in choices]}")
    result = register(app_id, bot_token, commands)
    print(f"Registered {len(result)} commands")


if __name__ == "__main__":
    main()
