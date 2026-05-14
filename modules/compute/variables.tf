# modules/compute/variables.tf

variable "project_name" {
  type    = string
  default = "agro-predict"
}

variable "environment" {
  type = string
}

variable "location" {
  description = "Región de Azure donde desplegar la VM"
  type        = string
}

variable "resource_group_name" {
  description = "Nombre del Resource Group donde crear la VM"
  type        = string
}

variable "instance_type" {
  description = "Tamaño de la VM en Azure. Standard_B1s es la opción más económica."
  type        = string
  default     = "Standard_B1s"
}

variable "subnet_id" {
  description = "ID de la subnet donde conectar la VM"
  type        = string
}

variable "public_ip_id" {
  description = "ID de la IP pública a asignar a la VM"
  type        = string
}

variable "ssh_public_key" {
  description = "Clave pública SSH para acceder a la VM. Genera con: ssh-keygen -t rsa -b 4096"
  type        = string
}

variable "github_org" {
  description = "Organización de GitHub donde está el repo de orquestación"
  type        = string
  default     = "agro-predict-tfg-2026"
}

variable "env_vars" {
  type      = map(string)
  sensitive = true
}
