# Data module: Aurora MySQL Global Database spanning the primary and
# recovery regions. The primary region creates the global cluster and the
# writer; the recovery region attaches a secondary cluster to the same
# global cluster and receives asynchronous replication. Promotion of the
# secondary is the mechanism behind the 1-minute RPO target in Figure 2.
#
# Prototype scope: the secondary is provisioned at reduced instance count
# for the assessment cost model. Aurora Global Database replicates
# asynchronously (typically under 1 second, but unmeasured here), so the
# RPO figure in the deck is a monitored design target, not a guarantee.

variable "project" {
  type = string
}

variable "environment" {
  type = string
}

variable "vpc_id" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "app_sg_id" {
  type = string
}

# Exactly one region in the root configuration sets is_primary = true.
variable "is_primary" {
  type    = bool
  default = false
}

# Name of the global cluster created in the primary region; required only
# when is_primary = false.
variable "primary_global_cluster_id" {
  type    = string
  default = ""
}

variable "instance_count" {
  type    = number
  default = 1
}

locals {
  global_cluster_id = var.is_primary ? aws_rds_global_cluster.this[0].id : data.aws_rds_global_cluster.primary[0].id
}

resource "aws_rds_global_cluster" "this" {
  count = var.is_primary ? 1 : 0

  global_cluster_identifier = "${var.project}-global"
  engine                    = "aurora-mysql"
  engine_version            = "8.0"
  storage_encrypted         = true

  tags = { Name = "${var.project}-${var.environment}-global" }
}

# The secondary region reads the global cluster created by the primary
# instead of creating it.
data "aws_rds_global_cluster" "primary" {
  count = var.is_primary ? 0 : 1

  global_cluster_identifier = var.primary_global_cluster_id
}

resource "aws_db_subnet_group" "this" {
  name       = "${var.project}-${var.environment}-db"
  subnet_ids = var.private_subnet_ids

  tags = { Name = "${var.project}-${var.environment}-db" }
}

resource "aws_security_group" "db" {
  name   = "${var.project}-${var.environment}-db-sg"
  vpc_id = var.vpc_id

  ingress {
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [var.app_sg_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project}-${var.environment}-db-sg" }
}

resource "aws_rds_cluster" "this" {
  cluster_identifier = "${var.project}-${var.environment}-aurora"
  engine             = "aurora-mysql"
  engine_version     = "8.0"
  engine_mode        = "provisioned"

  global_cluster_identifier = local.global_cluster_id

  database_name               = var.is_primary ? "nexora" : null
  master_username             = var.is_primary ? "nexora_admin" : null
  manage_master_user_password = var.is_primary

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.db.id]
  storage_encrypted      = true
  skip_final_snapshot    = true

  serverlessv2_scaling_configuration {
    min_capacity = 0.5
    max_capacity = 16
  }

  tags = { Name = "${var.project}-${var.environment}-aurora" }
}

resource "aws_rds_cluster_instance" "this" {
  count = var.instance_count

  identifier         = "${var.project}-${var.environment}-aurora-${count.index}"
  cluster_identifier = aws_rds_cluster.this.id
  instance_class     = "db.serverless"
  engine             = "aurora-mysql"
  engine_version     = "8.0"

  db_subnet_group_name         = aws_db_subnet_group.this.name
  performance_insights_enabled = true

  tags = { Name = "${var.project}-${var.environment}-aurora-${count.index}" }
}

output "global_cluster_id" {
  value = local.global_cluster_id
}

output "cluster_endpoint" {
  value = aws_rds_cluster.this.endpoint
}

output "reader_endpoint" {
  value = aws_rds_cluster.this.reader_endpoint
}
