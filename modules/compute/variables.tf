# modules/compute/variables.tf

variable "project_name" {
  type    = string
  default = "agro-predict"
}

variable "environment" {
  type = string
}

variable "instance_type" {
  description = "Tipo de instancia EC2. t2.micro es elegible para free tier."
  type        = string
  default     = "t2.micro"
}

variable "subnet_id" {
  description = "ID de la subnet donde lanzar la instancia"
  type        = string
}

variable "security_group_id" {
  description = "ID del security group a asociar"
  type        = string
}

variable "key_name" {
  description = "Nombre del key pair de AWS para acceso SSH (opcional en local)"
  type        = string
  default     = null
}

variable "github_org" {
  description = "Organización de GitHub donde está el repo de orquestación"
  type        = string
  default     = "agro-predict-tfg-2026"
}

variable "docker_image_tag" {
  description = "Tag de las imágenes Docker a desplegar"
  type        = string
  default     = "latest"
}

variable "env_vars" {
  type = map(string)
  sensitive = true
}
