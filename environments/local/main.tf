# environments/local/main.tf
# ─────────────────────────────────────────────────────────────────────────────
# Entorno LOCAL — apunta a LocalStack en lugar de AWS real.
# Usar para desarrollar y probar sin coste.
#
# Requisitos:
#   - LocalStack corriendo: ./scripts/start-localstack.sh
#
# Uso:
#   cd environments/local
#   terraform init
#   terraform apply
# ─────────────────────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Provider apuntando a LocalStack
provider "aws" {
  region                      = "us-east-1"
  access_key                  = "fake"   # LocalStack no valida credenciales reales
  secret_key                  = "fake"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    ec2            = "http://localhost:4566"
    s3             = "http://localhost:4566"
    secretsmanager = "http://localhost:4566"
  }
}

# ── Módulos ──────────────────────────────────────────────────────────────────

module "networking" {
  source = "../../modules/networking"

  environment  = "local"
  project_name = "agro-predict"
  aws_region   = "us-east-1"
  vpc_cidr     = "10.0.0.0/16"
  subnet_cidr  = "10.0.1.0/24"
}

module "compute" {
  source = "../../modules/compute"

  environment       = "local"
  project_name      = "agro-predict"
  subnet_id         = module.networking.subnet_id
  security_group_id = module.networking.security_group_id
  instance_type     = "t2.micro"
  github_org        = "agro-predict-tfg-2026"
}

module "storage" {
  source = "../../modules/storage"

  environment  = "local"
  project_name = "agro-predict"
}

module "secrets" {
  source = "../../modules/secrets"

  environment    = "local"
  project_name   = "agro-predict"
  aemet_api_key  = var.aemet_api_key
  itacyl_api_key = var.itacyl_api_key
}
