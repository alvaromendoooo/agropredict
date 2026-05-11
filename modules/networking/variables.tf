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

variable "aws_region" {
  description = "Región de AWS"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block para la VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr" {
  description = "CIDR block para la subnet pública"
  type        = string
  default     = "10.0.1.0/24"
}
