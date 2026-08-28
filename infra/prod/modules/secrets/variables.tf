# modules/secrets/variables.tf

variable "project_name" {
  type    = string
  default = "agro-predict"
}

variable "environment" {
  type = string
}

variable "resource_group_name" {
  description = "Nombre del Resource Group"
  type        = string
}

variable "location" {
  description = "Región de Azure"
  type        = string
}

variable "aemet_api_key" {
  description = "API key de AEMET"
  type        = string
  sensitive   = true
}

variable "itacyl_api_key" {
  description = "API key de ITACyL"
  type        = string
  sensitive   = true
}
