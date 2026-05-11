# modules/storage/outputs.tf

output "bucket_name" {
  description = "Nombre del bucket S3 de alertas"
  value       = aws_s3_bucket.alertas.id
}

output "bucket_arn" {
  description = "ARN del bucket, necesario para dar permisos IAM"
  value       = aws_s3_bucket.alertas.arn
}
