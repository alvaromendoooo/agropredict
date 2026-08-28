# modules/storage/main.tf
# ─────────────────────────────────────────────────────────────────────────────
# Azure Blob Storage para almacenar los logs de alertas.
# Equivalente al bucket S3 del entorno AWS.
# ─────────────────────────────────────────────────────────────────────────────

# Storage Account — contenedor de todos los recursos de almacenamiento en Azure
resource "azurerm_storage_account" "alertas" {
  name                     = "${replace(var.project_name, "-", "")}${var.environment}st"  # máx 24 chars, solo minúsculas y números
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"  # Locally Redundant Storage — equivalente a S3 standard

  # Bloquear acceso público — los logs no deben ser accesibles desde internet
  public_network_access_enabled = false

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Blob Container — equivalente al bucket S3
resource "azurerm_storage_container" "alertas" {
  name                  = "${var.project_name}-alertas"
  storage_account_name  = azurerm_storage_account.alertas.name
  container_access_type = "private"
}

# Lifecycle management — equivalente al lifecycle_configuration de S3
resource "azurerm_storage_management_policy" "alertas" {
  storage_account_id = azurerm_storage_account.alertas.id

  rule {
    name    = "archivar-logs-antiguos"
    enabled = true

    filters {
      blob_types = ["blockBlob"]
    }

    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than    = 30   # equivalente a STANDARD_IA
        delete_after_days_since_modification_greater_than          = 365  # borrar tras un año
      }
    }
  }
}
