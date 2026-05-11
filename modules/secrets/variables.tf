# modules/secrets/variables.tf

variable "project_name" {
  type    = string
  default = "agro-predict"
}

variable "environment" {
  type = string
}

variable "aemet_api_key" {
  description = "API key de AEMET. Pásala con TF_VAR_aemet_api_key o terraform.tfvars"
  type        = string
  sensitive   = true  # Terraform no la mostrará en los logs ni en el plan
}

variable "itacyl_api_key" {
  description = "API key de ITACyL"
  type        = string
  sensitive   = true
}
