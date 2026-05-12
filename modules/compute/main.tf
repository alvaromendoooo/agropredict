# modules/compute/main.tf
# ─────────────────────────────────────────────────────────────────────────────
# Instancia EC2 donde corren todos los servicios de Agro Predict via Docker.
# El user_data instala Docker automáticamente al arrancar la instancia,
# clona el repo de orchestration y lanza docker-compose.
# ─────────────────────────────────────────────────────────────────────────────

# Buscamos la AMI de Ubuntu 22.04 más reciente automáticamente
# Así no tenemos que hardcodear el ID de la AMI (que cambia por región)
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical (propietario oficial de Ubuntu en AWS)

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

locals {
  orchestator_env = templatefile(
    "${path.module}/orchestator.env.tpl",
    {
      siar_api_key = var.siar_api_key
      itacyl_api_key = var.itacyl_api_key
      aemet_api_key = var.aemet_api_key
      aemet_base_url = var.aemet_base_url
      mysql_root_password = var.mysql_root_password
      mysql_database = var.mysql_database
      mysql_user = var.mysql_user
      mysql_pasword = var.mysql_pasword
      redis_pass = var.redis_pass
      parallel = var.parallel
      models = var.models
      keep_alive = var.keep_alive
      mcp_server_url = var.mcp_server_url
      redis_host = var.redis_host
      redis_port = var.redis_port
      ollama_host = var.ollama_host
      ollama_model = var.ollama_model
      ollama_num_predict = var.ollama_num_predict
      rabbitmq_connection = var.rabbitmq_connection
      rabbitmq_host = var.rabbitmq_host
      queue_in_name = var.queue_in_name
      queue_out_name = var.queue_out_name
      rabbitmq_user = var.rabbitmq_user
      rabbitmq_pass = var.rabbitmq_pass
      sqlalchemy_database_url = var.sqlalchemy_database_url
      siar_service_data_url = var.siar_service_data_url
      siar_service_info_url = var.siar_service_info_url
      aemet_service_current_url = var.aemet_service_current_url
      aemet_service_future_url = var.aemet_service_future_url
      itacyl_service_base_url = var.itacyl_service_base_url
      dtagro_service_base_url = var.dtagro_service_base_url
      dtagro_api_token = var.dtagro_api_token
      data_service_historic_base_url = var.data_service_historic_base_url
      data_service_forecast_base_url = var.data_service_forecast_base_url
      data_service_crop_base_url = var.data_service_crop_base_url
      data_service_plagas_url = var.data_service_plagas_url
      data_service_sensores_base_url = var.data_service_sensores_base_url
      data_service_cultivos_base_url = var.data_service_cultivos_base_url
      password_certificado = var.password_certificado
      keycloak_secret = var.keycloak_secret
    }
  )
}

resource "aws_instance" "agro_predict" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type  # t2.micro en free tier
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [var.security_group_id]
  key_name               = var.key_name

  # user_data: script que se ejecuta automáticamente al arrancar la instancia
  # Instala Docker, clona el repo y lanza los servicios
  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    github_org   = var.github_org
    orchestator_env = locals.orchestator_env
  }))

  root_block_device {
    volume_size = 20  # GB — suficiente para Docker + imágenes
    volume_type = "gp3"
  }

  tags = {
    Name        = "${var.project_name}-server"
    Environment = var.environment
  }
}
