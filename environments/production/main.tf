# environments/production/main.tf
# ─────────────────────────────────────────────────────────────────────────────
# Entorno PRODUCTION — apunta a AWS real.
# Usar solo cuando la infraestructura esté probada en local.
#
# Requisitos:
#   - AWS CLI configurado: aws configure
#   - Las variables sensibles en terraform.tfvars (no subir a git)
#
# Uso:
#   cd environments/production
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

  # Recomendado: guardar el estado en S3 para no perderlo
  # Descomenta esto cuando tengas el bucket creado manualmente en AWS
  # backend "s3" {
  #   bucket = "agro-predict-terraform-state"
  #   key    = "production/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region
  # Las credenciales las lee de ~/.aws/credentials o variables de entorno
  # AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY — nunca hardcodear aquí
}

# ── Módulos ──────────────────────────────────────────────────────────────────

module "networking" {
  source = "../../modules/networking"

  environment  = "production"
  project_name = "agro-predict"
  aws_region   = var.aws_region
}

module "compute" {
  source = "../../modules/compute"

  environment       = "production"
  project_name      = "agro-predict"
  subnet_id         = module.networking.subnet_id
  security_group_id = module.networking.security_group_id
  instance_type     = "t2.micro"   # free tier eligible
  key_name          = var.key_name
  github_org        = "agro-predict-tfg-2026"
}

module "storage" {
  source = "../../modules/storage"

  environment  = "production"
  project_name = "agro-predict"
}

module "secrets" {
  source = "../../modules/secrets"

  environment    = "production"
  project_name   = "agro-predict"
  aemet_api_key  = var.aemet_api_key
  itacyl_api_key = var.itacyl_api_key
}
