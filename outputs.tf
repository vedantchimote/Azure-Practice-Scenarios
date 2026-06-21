# =============================================================================
# Outputs — Key Information After Deployment
# =============================================================================
# These values are displayed after 'terraform apply' completes.

output "resource_group_name" {
  description = "Name of the Azure Resource Group"
  value       = azurerm_resource_group.main.name
}

output "vnet_name" {
  description = "Name of the Virtual Network"
  value       = azurerm_virtual_network.main.name
}

output "vnet_address_space" {
  description = "Address space of the VNet"
  value       = azurerm_virtual_network.main.address_space
}

output "public_subnet_id" {
  description = "Resource ID of the public subnet"
  value       = azurerm_subnet.public.id
}

output "private_subnet_id" {
  description = "Resource ID of the private subnet"
  value       = azurerm_subnet.private.id
}

output "load_balancer_public_ip" {
  description = "Public IP address of the Load Balancer — open this in a browser!"
  value       = azurerm_public_ip.lb.ip_address
}

output "website_url" {
  description = "URL to access the deployed webpage"
  value       = "http://${azurerm_public_ip.lb.ip_address}"
}

output "vm_names" {
  description = "Names of all deployed web server VMs"
  value       = azurerm_linux_virtual_machine.web[*].name
}

output "vm_private_ips" {
  description = "Private IP addresses of the web server VMs"
  value       = azurerm_network_interface.web[*].private_ip_address
}

output "ssh_commands" {
  description = "SSH commands to connect to each VM via the Load Balancer NAT rules"
  value = [
    for i in range(var.vm_count) :
    "ssh -p ${50001 + i} ${var.admin_username}@${azurerm_public_ip.lb.ip_address}"
  ]
}
