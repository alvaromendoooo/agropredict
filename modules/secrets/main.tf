# modules/secrets/main.tf
# ─────────────────────────────────────────────────────────────────────────────
# Azure Key Vault para gestión de secretos.
# Equivalente a AWS Secrets Manager.
# Solo almacena las API keys externas (AEMET, ITACyL, SiAR).
# El resto de variables se inyectan vía user_data como en el entorno local.
# ─────────────────────────────────────────────────────────────────────────────

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "main" {
  name                = "${var.project_name}-kv-prod"
  location            = var.location
  resource_group_name = var.resource_group_name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  # Permitir acceso al service principal de Terraform
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = ["Get", "Set", "Delete", "List", "Purge"]
  }

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_key_vault_secret" "aemet_api_key" {
  name         = "aemet-api-key"
  value        = var.aemet_api_key
  key_vault_id = azurerm_key_vault.main.id
}

resource "azurerm_key_vault_secret" "itacyl_api_key" {
  name         = "itacyl-api-key"
  value        = var.itacyl_api_key
  key_vault_id = azurerm_key_vault.main.id
}
