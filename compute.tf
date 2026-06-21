# =============================================================================
# Virtual Machines — Apache Web Servers
# =============================================================================
# This file creates:
#   1. An Availability Set for high availability across fault/update domains
#   2. Network Interfaces (one per VM) associated with the LB backend pool
#   3. Linux VMs with Ubuntu 22.04 LTS running Apache2 (installed via cloud-init)
#
# The VMs do NOT get public IPs — all inbound traffic flows through the LB.
# SSH access is possible via the LB's public IP + NAT rules (see nat_rules.tf).

# ---- Availability Set ----
# Ensures VMs are spread across different physical fault domains and update domains

resource "azurerm_availability_set" "web" {
  name                         = "${local.name_prefix}-avset"
  location                     = azurerm_resource_group.main.location
  resource_group_name          = azurerm_resource_group.main.name
  platform_fault_domain_count  = 2
  platform_update_domain_count = 5
  managed                      = true
  tags                         = local.tags
}

# ---- Network Interfaces ----
# Each VM gets a NIC in the public subnet, associated with the LB backend pool

resource "azurerm_network_interface" "web" {
  count               = var.vm_count
  name                = "${local.name_prefix}-web-nic-${count.index + 1}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  tags                = local.tags

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.public.id
    private_ip_address_allocation = "Dynamic"
    # No public IP — traffic comes through the Load Balancer
  }
}

# ---- Associate NICs with LB Backend Pool ----

resource "azurerm_network_interface_backend_address_pool_association" "web" {
  count                   = var.vm_count
  network_interface_id    = azurerm_network_interface.web[count.index].id
  ip_configuration_name   = "internal"
  backend_address_pool_id = azurerm_lb_backend_address_pool.web.id
}

# ---- Linux Virtual Machines ----

resource "azurerm_linux_virtual_machine" "web" {
  count               = var.vm_count
  name                = "${local.name_prefix}-web-vm-${count.index + 1}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  size                = var.vm_size
  availability_set_id = azurerm_availability_set.web.id
  tags = merge(local.tags, {
    Role = "WebServer"
    VM   = "web-${count.index + 1}"
  })

  # Admin credentials
  admin_username                  = var.admin_username
  admin_password                  = var.admin_password
  disable_password_authentication = false

  # Attach the NIC
  network_interface_ids = [
    azurerm_network_interface.web[count.index].id
  ]

  # OS Disk
  os_disk {
    name                 = "${local.name_prefix}-web-osdisk-${count.index + 1}"
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
    disk_size_gb         = 30
  }

  # Ubuntu 22.04 LTS Image
  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  # Cloud-init script to install Apache and deploy a landing page
  # The custom_data must be base64-encoded — Terraform's base64encode() handles this
  custom_data = base64encode(templatefile("${path.module}/scripts/cloud-init.yaml", {
    vm_name  = "${local.name_prefix}-web-vm-${count.index + 1}"
    vm_index = count.index + 1
  }))
}
