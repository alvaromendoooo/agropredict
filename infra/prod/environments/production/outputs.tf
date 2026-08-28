# environments/production/outputs.tf

output "public_ip" {
  description = "IP pública de la VM — úsala para conectarte por SSH: ssh azureuser@<ip>"
  value       = module.networking.public_ip_address
}

output "instance_id" {
  description = "ID de la VM en Azure"
  value       = module.compute.instance_id
}

output "storage_account_name" {
  description = "Nombre del Storage Account de alertas"
  value       = module.storage.storage_account_name
}

output "resource_group" {
  description = "Resource Group que contiene toda la infraestructura"
  value       = module.networking.resource_group_name
}
