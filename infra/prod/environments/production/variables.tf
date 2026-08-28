# environments/production/variables.tf

variable "azure_subscription_id" {
  description = "ID de la suscripción de Azure"
  type        = string
  sensitive   = true
}

variable "azure_region" {
  description = "Región de Azure donde desplegar"
  type        = string
  default     = "West Europe"
}

variable "ssh_public_key" {
  description = "Clave pública SSH para acceder a la VM. Genera con: ssh-keygen -t rsa -b 4096 -f ~/.ssh/agro-predict"
  type        = string
}

variable "env_vars" {
  description = "Variables de entorno para los contenedores Docker"
  type        = map(string)
  sensitive   = true
}
