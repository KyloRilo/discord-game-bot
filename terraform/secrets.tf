resource "aws_secretsmanager_secret" "discord" {
  name = "${var.project}/discord"

  tags = {
    Project     = var.project
  }
}

resource "aws_secretsmanager_secret_version" "discord" {
  secret_id = aws_secretsmanager_secret.discord.id

  secret_string = jsonencode({
    bot_token       = var.discord_bot_token
    application_id  = var.discord_application_id
    public_key      = var.discord_public_key
  })
}