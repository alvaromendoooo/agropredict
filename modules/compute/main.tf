# modules/compute/main.tf
# ─────────────────────────────────────────────────────────────────────────────
# Instancia EC2 donde corren todos los servicios de Agro Predict via Docker.
# El user_data instala Docker automáticamente al arrancar la instancia,
# clona el repo de orchestration y lanza docker-compose.
# ─────────────────────────────────────────────────────────────────────────────

# Buscamos la AMI de Ubuntu 22.04 más reciente automáticamente
# Así no tenemos que hardcodear el ID de la AMI (que cambia por región)
/*data "aws_ami" "ubuntu" {
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
}*/ // Descomentar para entorno producción

locals {
  orchestator_env = templatefile(
    "${path.module}/orchestator.env.tpl",
    var.env_vars
  )
}

resource "aws_instance" "agro_predict" {
  ami                    = "ami-000000000000"
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [var.security_group_id]
  key_name               = var.key_name

  user_data = base64encode(templatefile("${path.module}/user_data.sh", {
    github_org      = var.github_org
    orchestator_env = local.orchestator_env
  }))

  /*root_block_device {
    volume_size = 20 # GB — suficiente para Docker + imágenes
    volume_type = "gp3"
  }*/ # Descomentar en produccion
  tags = {
    Name        = "${var.project_name}-server"
    Environment = var.environment
  }
}

