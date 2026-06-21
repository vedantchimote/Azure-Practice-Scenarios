# =============================================================================
# NAT Rules — SSH Access to Individual VMs via Load Balancer
# =============================================================================
# Since VMs don't have public IPs, we create Inbound NAT Rules on the LB
# to allow SSH access to each VM on unique ports:
#
#   VM-1:  LB_PUBLIC_IP:50001  →  VM-1:22
#   VM-2:  LB_PUBLIC_IP:50002  →  VM-2:22
#
# Usage:  ssh -p 50001 azureadmin@<LB_PUBLIC_IP>

resource "azurerm_lb_nat_rule" "ssh" {
  count                          = var.vm_count
  name                           = "${local.name_prefix}-ssh-nat-vm-${count.index + 1}"
  resource_group_name            = azurerm_resource_group.main.name
  loadbalancer_id                = azurerm_lb.web.id
  protocol                       = "Tcp"
  frontend_port                  = 50001 + count.index
  backend_port                   = 22
  frontend_ip_configuration_name = "web-frontend"
}

resource "azurerm_network_interface_nat_rule_association" "ssh" {
  count                 = var.vm_count
  network_interface_id  = azurerm_network_interface.web[count.index].id
  ip_configuration_name = "internal"
  nat_rule_id           = azurerm_lb_nat_rule.ssh[count.index].id
}
