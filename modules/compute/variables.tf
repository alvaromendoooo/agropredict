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

# Variables con las que cargar el .env para la EC2
variable "siar_api_key" {
  sensitive = true
}

variable "itacyl_api_key" {
  sensitive = true
}

variable "aemet_api_key" {
  sensitive = true
}

variable "aemet_base_url" {
  sensitive = true
}

variable "mysql_root_password" {
  sensitive = true
}

variable "mysql_database" {
  sensitive = true
}

variable "mysql_user" {
  sensitive = true
}

variable "mysql_pasword" {
  sensitive = true
}

variable "redis_pass" {
  sensitive = true
}

variable "parallel" {
  sensitive = true
}

variable "models" {
  sensitive = true
}

variable "keep_alive" {
  sensitive = true
}

variable "mcp_server_url" {
  sensitive = true
}

variable "redis_host" {
  sensitive = true
}

variable "redis_port" {
  sensitive = true
}

variable "ollama_host" {
  sensitive = true
}

variable "ollama_model" {
  sensitive = true
}

variable "ollama_num_predict" {
  sensitive = true
}

variable "rabbitmq_connection" {
  sensitive = true
}

variable "rabbitmq_host" {
  sensitive = true
}

variable "queue_in_name" {
  sensitive = true
}

variable "queue_out_name" {
  sensitive = true
}

variable "rabbitmq_user" {
  sensitive = true
}

variable "rabbitmq_pass" {
  sensitive = true
}

variable "sqlalchemy_database_url" {
  sensitive = true
}

variable "siar_service_data_url" {
  sensitive = true
}

variable "siar_service_info_url" {
  sensitive = true
}

variable "aemet_service_current_url" {
  sensitive = true
}

variable "aemet_service_future_url" {
  sensitive = true
}

variable "itacyl_service_base_url" {
  sensitive = true
}

variable "dtagro_service_base_url" {
  sensitive = true
}

variable "dtagro_api_token" {
  sensitive = true
}

variable "data_service_historic_base_url" {
  sensitive = true
}

variable "data_service_forecast_base_url" {
  sensitive = true
}

variable "data_service_crop_base_url" {
  sensitive = true
}

variable "data_service_plagas_url" {
  sensitive = true
}

variable "data_service_sensores_base_url" {
  sensitive = true
}

variable "data_service_cultivos_base_url" {
  sensitive = true
}

variable "password_certificado" {
  sensitive = true
}

variable "keycloak_secret" {
  sensitive = true
}