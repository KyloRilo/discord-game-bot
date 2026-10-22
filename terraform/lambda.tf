data "aws_caller_identity" "current" {}

resource "aws_iam_role" "discord_bot_lambda" {
  name = "${var.project}-discord-bot-lambda"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.discord_bot_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "discord_bot" {
  name = "${var.project}-discord-bot"
  role = aws_iam_role.discord_bot_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecs:RunTask",
          "ecs:StopTask",
          "ecs:DescribeTasks",
          "ecs:ListTasks"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = "iam:PassRole"
        Resource = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/${var.project}-*"
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:CreateSecret",
          "secretsmanager:DeleteSecret",
          "secretsmanager:GetSecretValue",
          "secretsmanager:PutSecretValue"
        ]
        Resource = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:${var.project}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "events:PutRule",
          "events:DeleteRule",
          "events:PutTargets",
          "events:RemoveTargets"
        ]
        Resource = "arn:aws:events:${var.aws_region}:${data.aws_caller_identity.current.account_id}:rule/${var.project}-*"
      },
      {
        Effect = "Allow"
        Action = [
          "backup:StartBackupJob",
          "backup:DescribeBackupJob",
          "backup:ListBackupJobs"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.game_config.arn,
          "${aws_s3_bucket.game_config.arn}/*"
        ]
      }
    ]
  })
}

# resource "aws_lambda_function" "discord_bot" {
#   function_name = "${var.project}-discord-bot"
#   role          = aws_iam_role.discord_bot_lambda.arn
#   package_type  = "Image"
#   image_uri     = "${aws_ecr_repository.discord_bot.repository_url}:${var.discord_bot_image_tag}"
#   timeout       = 30
#   memory_size   = 256

#   environment {
#     variables = {
#       PROJECT       = var.project
#       CONFIG_BUCKET = aws_s3_bucket.game_config.bucket
#     }
#   }
# }

# resource "aws_lambda_function_url" "discord_bot" {
#   function_name      = aws_lambda_function.discord_bot.function_name
#   authorization_type = "NONE"
# }
