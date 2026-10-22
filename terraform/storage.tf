resource "aws_efs_file_system" "game_data" {
  encrypted = true

  tags = {
    Name    = "${var.project}-game-data"
    Project = var.project
  }
}

resource "aws_efs_mount_target" "game_data" {
  for_each = toset(aws_subnet.private[*].id)

  file_system_id  = aws_efs_file_system.game_data.id
  subnet_id       = each.value
  security_groups = [aws_security_group.efs.id]
}

resource "aws_security_group" "efs" {
  name_prefix = "${var.project}-efs-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-efs"
  }
}

resource "aws_security_group" "ecs_tasks" {
  name_prefix = "${var.project}-ecs-tasks-"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-ecs-tasks"
  }
}

resource "aws_backup_vault" "game_data" {
  name = "${var.project}-game-data"
}
