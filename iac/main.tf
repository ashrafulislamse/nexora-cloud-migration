# NEXORA multi-region prototype (BIT4043 Final Assessment)
#
# Assessment prototype, not production configuration. It demonstrates the
# module structure behind Figure 2 (To-Be): primary region ap-southeast-5,
# recovery region ap-southeast-3.
#
# Primary region: VPC, security/IAM, Fargate storefront (2-20 tasks),
# Aurora Serverless v2 cluster joined to the Aurora Global Database, and
# monitoring.
#
# Recovery region: VPC baseline, the same security stack, a scaled-down
# warm-standby Fargate service (1-4 tasks), a secondary Aurora cluster
# attached to the global cluster (asynchronous replication from the
# primary writer), and its own alarms.

terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  alias  = "primary"
  region = var.primary_region
}

provider "aws" {
  alias  = "recovery"
  region = var.recovery_region
}

module "networking_primary" {
  source = "./modules/networking"

  project     = "nexora"
  environment = "primary"
  vpc_cidr    = var.primary_vpc_cidr
  az_count    = 2

  providers = {
    aws = aws.primary
  }
}

module "networking_recovery" {
  source = "./modules/networking"

  project     = "nexora"
  environment = "recovery"
  vpc_cidr    = var.recovery_vpc_cidr
  az_count    = 2

  providers = {
    aws = aws.recovery
  }
}

module "security_primary" {
  source = "./modules/security"

  project     = "nexora"
  environment = "primary"
  vpc_id      = module.networking_primary.vpc_id
  app_port    = var.app_port

  providers = {
    aws = aws.primary
  }
}

module "security_recovery" {
  source = "./modules/security"

  project     = "nexora"
  environment = "recovery"
  vpc_id      = module.networking_recovery.vpc_id
  app_port    = var.app_port

  providers = {
    aws = aws.recovery
  }
}

module "data_primary" {
  source = "./modules/data"

  project            = "nexora"
  environment        = "primary"
  vpc_id             = module.networking_primary.vpc_id
  private_subnet_ids = module.networking_primary.private_subnet_ids
  app_sg_id          = module.security_primary.app_sg_id
  is_primary         = true
  instance_count     = 2

  providers = {
    aws = aws.primary
  }
}

module "compute_primary" {
  source = "./modules/compute"

  project            = "nexora"
  environment        = "primary"
  vpc_id             = module.networking_primary.vpc_id
  public_subnet_ids  = module.networking_primary.public_subnet_ids
  private_subnet_ids = module.networking_primary.private_subnet_ids
  alb_sg_id          = module.security_primary.alb_sg_id
  app_sg_id          = module.security_primary.app_sg_id
  execution_role_arn = module.security_primary.execution_role_arn
  task_role_arn      = module.security_primary.task_role_arn
  app_image          = var.app_image
  app_port           = var.app_port
  min_tasks          = var.min_tasks
  max_tasks          = var.max_tasks

  providers = {
    aws = aws.primary
  }
}

module "monitoring_primary" {
  source = "./modules/monitoring"

  project      = "nexora"
  environment  = "primary"
  cluster_name = module.compute_primary.cluster_name
  service_name = module.compute_primary.service_name
  alarm_email  = var.alarm_email

  providers = {
    aws = aws.primary
  }
}

module "compute_recovery" {
  source = "./modules/compute"

  project            = "nexora"
  environment        = "recovery"
  vpc_id             = module.networking_recovery.vpc_id
  public_subnet_ids  = module.networking_recovery.public_subnet_ids
  private_subnet_ids = module.networking_recovery.private_subnet_ids
  alb_sg_id          = module.security_recovery.alb_sg_id
  app_sg_id          = module.security_recovery.app_sg_id
  execution_role_arn = module.security_recovery.execution_role_arn
  task_role_arn      = module.security_recovery.task_role_arn
  app_image          = var.app_image
  app_port           = var.app_port
  min_tasks          = 1
  max_tasks          = 4

  providers = {
    aws = aws.recovery
  }
}

module "data_recovery" {
  source = "./modules/data"

  project                   = "nexora"
  environment               = "recovery"
  vpc_id                    = module.networking_recovery.vpc_id
  private_subnet_ids        = module.networking_recovery.private_subnet_ids
  app_sg_id                 = module.security_recovery.app_sg_id
  is_primary                = false
  primary_global_cluster_id = module.data_primary.global_cluster_id
  instance_count            = 1

  providers = {
    aws = aws.recovery
  }
}

module "monitoring_recovery" {
  source = "./modules/monitoring"

  project      = "nexora"
  environment  = "recovery"
  cluster_name = module.compute_recovery.cluster_name
  service_name = module.compute_recovery.service_name
  alarm_email  = var.alarm_email

  providers = {
    aws = aws.recovery
  }
}
