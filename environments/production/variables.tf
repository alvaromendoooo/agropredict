# environments/production/variables.tf

variable "aws_region" {
  description = "Región de AWS donde desplegar"
  type        = string
  default     = "us-east-1"
}

variable "key_name" {
  description = "Nombre del key pair de AWS para acceso SSH a la instancia"
  type        = string
}

variable "aemet_api_key" {
  description = "API key real de AEMET"
  type        = string
  sensitive   = true
}

variable "itacyl_api_key" {
  description = "API key real de ITACyL"
  type        = string
  sensitive   = true
}
