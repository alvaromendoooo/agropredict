# modules/compute/outputs.tf

output "instance_id" {
  description = "ID de la VM en Azure"
  value       = azurerm_linux_virtual_machine.agro_predict.id
}

output "public_ip" {
  description = "IP pública de la VM — úsala para conectarte por SSH"
  value       = azurerm_network_interface.main.private_ip_address
}
