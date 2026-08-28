# environments/production/main.tf

terraform {
  required_version = ">= 1.5"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.1.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.azure_subscription_id
  resource_provider_registrations = "none"
}

# ── Módulos ──────────────────────────────────────────────────────────────────

module "networking" {
  source = "../../modules/networking"

  environment  = "production"
  project_name = "agro-predict"
  location     = var.azure_region
}

module "compute" {
  source = "../../modules/compute"

  environment         = "production"
  project_name        = "agro-predict"
  location            = module.networking.location
  resource_group_name = module.networking.resource_group_name
  subnet_id           = module.networking.subnet_id
  public_ip_id        = module.networking.public_ip_id
  instance_type       = "Standard_B1s"
  ssh_public_key      = var.ssh_public_key
  github_org          = "agro-predict-tfg-2026"
  env_vars            = var.env_vars
  # security_group_id eliminado — en Azure el NSG se asocia a la subnet, no a la VM
}

module "storage" {
  source = "../../modules/storage"

  environment         = "production"
  project_name        = "agro-predict"
  location            = module.networking.location
  resource_group_name = module.networking.resource_group_name
}

module "secrets" {
  source = "../../modules/secrets"

  environment         = "production"
  project_name        = "agro-predict"
  location            = module.networking.location            # typo corregido
  resource_group_name = module.networking.resource_group_name
  aemet_api_key       = var.env_vars["aemet_api_key"]
  itacyl_api_key      = var.env_vars["itacyl_api_key"]
}