# =============================================================================
# Load Balancer — Public-facing L4 Load Balancer
# =============================================================================
# This creates an Azure Standard Load Balancer that distributes HTTP traffic
# across the web server VMs in the public subnet.
#
# Architecture:
#   Internet → Public IP → LB Frontend → LB Rule → Backend Pool → VMs
#                                           ↳ Health Probe (HTTP /index.html)

# ---- Public IP for the Load Balancer ----

resource "azurerm_public_ip" "lb" {
  name                = "${local.name_prefix}-lb-pip"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  allocation_method   = "Static"
  sku                 = "Standard"
  tags                = local.tags
}

# ---- Load Balancer ----

resource "azurerm_lb" "web" {
  name                = "${local.name_prefix}-lb"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "Standard"
  tags                = local.tags

  frontend_ip_configuration {
    name                 = "web-frontend"
    public_ip_address_id = azurerm_public_ip.lb.id
  }
}

# ---- Backend Address Pool ----
# VMs will be associated with this pool via their NICs

resource "azurerm_lb_backend_address_pool" "web" {
  name            = "${local.name_prefix}-backend-pool"
  loadbalancer_id = azurerm_lb.web.id
}

# ---- Health Probe ----
# The LB checks each VM's health by hitting HTTP port 80 every 5 seconds.
# A VM is marked unhealthy after 2 consecutive failures.

resource "azurerm_lb_probe" "http" {
  name                = "${local.name_prefix}-http-probe"
  loadbalancer_id     = azurerm_lb.web.id
  protocol            = "Http"
  port                = 80
  request_path        = "/index.html"
  interval_in_seconds = 5
  number_of_probes    = 2
}

# ---- Load Balancing Rule ----
# Routes inbound port 80 traffic to backend pool port 80

resource "azurerm_lb_rule" "http" {
  name                           = "${local.name_prefix}-http-rule"
  loadbalancer_id                = azurerm_lb.web.id
  protocol                       = "Tcp"
  frontend_port                  = 80
  backend_port                   = 80
  frontend_ip_configuration_name = "web-frontend"
  backend_address_pool_ids       = [azurerm_lb_backend_address_pool.web.id]
  probe_id                       = azurerm_lb_probe.http.id
  disable_outbound_snat          = true
  idle_timeout_in_minutes        = 4
}

# ---- Outbound Rule ----
# Allows VMs behind the Standard LB to reach the internet (for apt-get, etc.)

resource "azurerm_lb_outbound_rule" "web" {
  name                    = "${local.name_prefix}-outbound-rule"
  loadbalancer_id         = azurerm_lb.web.id
  protocol                = "All"
  backend_address_pool_id = azurerm_lb_backend_address_pool.web.id

  frontend_ip_configuration {
    name = "web-frontend"
  }
}
