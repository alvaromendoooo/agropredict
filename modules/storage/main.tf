# modules/storage/main.tf
# ─────────────────────────────────────────────────────────────────────────────
# Bucket S3 para almacenar los logs de alertas que genera log_alertas()
# en prediction_service.py — en lugar de escribirlos en fichero local.
# ─────────────────────────────────────────────────────────────────────────────

resource "aws_s3_bucket" "alertas" {
  # Los nombres de bucket S3 son globales en AWS, por eso añadimos sufijo único
  bucket = "${var.project_name}-alertas-${var.environment}"

  tags = {
    Name        = "${var.project_name}-alertas"
    Environment = var.environment
  }
}

# Bloquear acceso público — los logs no deben ser accesibles desde internet
resource "aws_s3_bucket_public_access_block" "alertas" {
  bucket = aws_s3_bucket.alertas.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Ciclo de vida: mover logs antiguos a almacenamiento más barato automáticamente
resource "aws_s3_bucket_lifecycle_configuration" "alertas" {
  bucket = aws_s3_bucket.alertas.id

  rule {
    id     = "archivar-logs-antiguos"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"  # más barato para datos poco accedidos
    }

    expiration {
      days = 365  # borrar logs con más de un año
    }
  }
}
