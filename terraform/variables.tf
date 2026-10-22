variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project" {
  type    = string
  default = "game-bot"
}

variable "discord_bot_image_tag" {
  type    = string
  default = "latest"
}

variable "discord_bot_token" {
  type      = string
  sensitive = true
}

variable "discord_application_id" {
  type      = string
  sensitive = true
}

variable "discord_public_key" {
  type      = string
  sensitive = true
}