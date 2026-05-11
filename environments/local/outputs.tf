# environments/local/outputs.tf

output "instance_id" {
  description = "ID de la instancia EC2 en LocalStack"
  value       = module.compute.instance_id
}

output "public_ip" {
  description = "IP pública simulada por LocalStack"
  value       = module.compute.public_ip
}

output "bucket_name" {
  description = "Nombre del bucket S3 de alertas"
  value       = module.storage.bucket_name
}
