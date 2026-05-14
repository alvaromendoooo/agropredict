# modules/networking/outputs.tf

output "resource_group_name" {
  description = "Nombre del Resource Group"
  value       = azurerm_resource_group.main.name
}

output "subnet_id" {
  description = "ID de la subnet pública"
  value       = azurerm_subnet.public.id
}

output "nsg_id" {
  description = "ID del Network Security Group"
  value       = azurerm_network_security_group.main.id
}

output "public_ip_id" {
  description = "ID de la IP pública"
  value       = azurerm_public_ip.main.id
}

output "public_ip_address" {
  description = "Dirección IP pública"
  value       = azurerm_public_ip.main.ip_address
}

output "location" {
  description = "Región de Azure donde se despliega"
  value       = azurerm_resource_group.main.location
}
