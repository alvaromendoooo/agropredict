# modules/networking/variables.tf

variable "project_name" {
  description = "Nombre del proyecto, usado para etiquetar recursos"
  type        = string
  default     = "agro-predict"
}

variable "environment" {
  description = "Entorno de despliegue (local, production)"
  type        = string
}

variable "location" {
  description = "Región de Azure donde desplegar los recursos"
  type        = string
  default     = "West Europe"
}

variable "vpc_cidr" {
  description = "CIDR block para la Virtual Network"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr" {
  description = "CIDR block para la subnet pública"
  type        = string
  default     = "10.0.1.0/24"
}
