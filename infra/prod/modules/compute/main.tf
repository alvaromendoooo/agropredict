# modules/compute/main.tf
# ─────────────────────────────────────────────────────────────────────────────
# VM Linux en Azure donde corren todos los servicios de Agro Predict via Docker.
# El custom_data (equivalente al user_data de AWS) instala Docker al arrancar,
# clona el repo de orquestación y lanza docker-compose.
# ─────────────────────────────────────────────────────────────────────────────

locals {
  orchestator_env = templatefile(
    "${path.module}/orchestator.env.tpl",
    var.env_vars
  )
}

# Network Interface — conecta la VM a la subnet y le asigna la IP pública
resource "azurerm_network_interface" "main" {
  name                = "${var.project_name}-nic"
  location            = var.location
  resource_group_name = var.resource_group_name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = var.subnet_id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = var.public_ip_id
  }

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_linux_virtual_machine" "agro_predict" {
  name                = "${var.project_name}-vm"
  location            = var.location
  resource_group_name = var.resource_group_name
  size                = var.instance_type  # Equivalente a instance_type en AWS
  admin_username      = "azureuser"

  # custom_data es el equivalente al user_data de AWS EC2
  custom_data = base64encode(templatefile("${path.module}/user_data.sh", {
    github_org      = var.github_org
    orchestator_env = local.orchestator_env
  }))

  network_interface_ids = [azurerm_network_interface.main.id]

  # Autenticación SSH con clave pública (más seguro que contraseña)
  admin_ssh_key {
    username   = "azureuser"
    public_key = var.ssh_public_key
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"  # Equivalente a gp2 en AWS
    disk_size_gb         = 30
  }

  # Ubuntu 22.04 LTS — mismo SO que en el entorno AWS
  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  tags = {
    Name        = "${var.project_name}-server"
    Environment = var.environment
  }
}
