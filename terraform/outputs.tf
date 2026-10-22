output "ecr_valheim_url" {
  value = aws_ecr_repository.valheim.repository_url
}

output "ecr_discord_bot_url" {
  value = aws_ecr_repository.discord_bot.repository_url
}

output "lambda_function_url" {
  value = aws_lambda_function_url.discord_bot.function_url
}

output "lambda_role_arn" {
  value = aws_iam_role.discord_bot_lambda.arn
}

output "efs_file_system_id" {
  value = aws_efs_file_system.game_data.id
}

output "ecs_tasks_security_group_id" {
  value = aws_security_group.ecs_tasks.id
}

output "config_bucket_name" {
  value = aws_s3_bucket.game_config.bucket
}
