# modules/storage/outputs.tf

output "storage_account_name" {
  description = "Nombre del Storage Account (equivalente al bucket name en S3)"
  value       = azurerm_storage_account.alertas.name
}

output "container_name" {
  description = "Nombre del Blob Container"
  value       = azurerm_storage_container.alertas.name
}
