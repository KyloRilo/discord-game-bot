resource "aws_s3_bucket" "game_config" {
  bucket = "${var.project}-game-config"

  tags = {
    Name    = "${var.project}-game-config"
    Project = var.project
  }
}

resource "aws_s3_bucket_versioning" "game_config" {
  bucket = aws_s3_bucket.game_config.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "game_config" {
  bucket = aws_s3_bucket.game_config.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
