# environments/production/outputs.tf

output "instance_id" {
  value = module.compute.instance_id
}

output "public_ip" {
  description = "IP pública de la instancia — úsala para conectarte por SSH"
  value       = module.compute.public_ip
}

output "bucket_name" {
  value = module.storage.bucket_name
}
