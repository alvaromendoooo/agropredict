# modules/secrets/main.tf
# ─────────────────────────────────────────────────────────────────────────────
# Gestión de secretos con AWS Secrets Manager.
# Sustituye los ficheros .env con API keys en texto plano.
# Los servicios leen los secretos en tiempo de ejecución via AWS SDK.
# ─────────────────────────────────────────────────────────────────────────────

# Secreto para la API key de AEMET
resource "aws_secretsmanager_secret" "aemet_api_key" {
  name        = "${var.project_name}/${var.environment}/aemet-api-key"
  description = "API key para el servicio de AEMET"

  tags = {
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "aemet_api_key" {
  secret_id     = aws_secretsmanager_secret.aemet_api_key.id
  # El valor real se pasa como variable — nunca hardcodeado aquí
  secret_string = var.aemet_api_key
}

# Secreto para la API key de ITACyL (plagas)
resource "aws_secretsmanager_secret" "itacyl_api_key" {
  name        = "${var.project_name}/${var.environment}/itacyl-api-key"
  description = "API key para el servicio de ITACyL"

  tags = {
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "itacyl_api_key" {
  secret_id     = aws_secretsmanager_secret.itacyl_api_key.id
  secret_string = var.itacyl_api_key
}
