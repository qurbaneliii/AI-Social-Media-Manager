terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.70"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "network" {
  source = "./modules/network"
  name   = "aria"
  cidr   = "10.50.0.0/16"
}

module "security" {
  source = "./modules/security"
  name   = "aria"
}

resource "aws_s3_bucket" "media" {
  bucket = "aria-media-${var.environment}"
}

resource "aws_kms_key" "aria" {
  description         = "ARIA envelope encryption key"
  enable_key_rotation = true
}

resource "aws_secretsmanager_secret" "app" {
  name = "/aria/${var.environment}/app"
}

resource "aws_db_instance" "postgres" {
  identifier              = "aria-postgres-${var.environment}"
  allocated_storage       = 100
  engine                  = "postgres"
  engine_version          = "15"
  instance_class          = "db.m6g.large"
  username                = var.db_username
  password                = var.db_password
  skip_final_snapshot     = true
  publicly_accessible     = false
  db_subnet_group_name    = module.network.db_subnet_group_name
  vpc_security_group_ids  = [module.security.db_sg_id]
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "aria-redis-${var.environment}"
  description                = "ARIA redis cache"
  node_type                  = "cache.t4g.medium"
  engine                     = "redis"
  automatic_failover_enabled = true
  num_cache_clusters         = 2
}
