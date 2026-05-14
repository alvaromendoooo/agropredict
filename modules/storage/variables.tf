# modules/storage/variables.tf

variable "project_name" {
  type    = string
  default = "agro-predict"
}

variable "environment" {
  type = string
}

variable "resource_group_name" {
  description = "Nombre del Resource Group donde crear el storage"
  type        = string
}

variable "location" {
  description = "Región de Azure"
  type        = string
}
