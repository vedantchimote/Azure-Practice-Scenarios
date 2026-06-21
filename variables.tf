# =============================================================================
# Variable Definitions
# =============================================================================
# All configurable parameters for the infrastructure are defined here.
# Override defaults via terraform.tfvars or -var flags.

# ---- General ----

variable "project_name" {
  description = "A short name used as a prefix for all resources"
  type        = string
  default     = "webdemo"
}

variable "environment" {
  description = "Deployment environment tag (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region where all resources will be deployed"
  type        = string
  default     = "Central India"
}

# ---- Networking ----

variable "vnet_address_space" {
  description = "Address space for the Virtual Network (CIDR block)"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "public_subnet_prefix" {
  description = "CIDR block for the public-facing subnet (web tier)"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_prefix" {
  description = "CIDR block for the private/backend subnet (reserved for future use)"
  type        = string
  default     = "10.0.2.0/24"
}

# ---- Virtual Machines ----

variable "vm_count" {
  description = "Number of web server VMs to deploy behind the load balancer"
  type        = number
  default     = 2
}

variable "vm_size" {
  description = "Azure VM size (SKU) for the web servers"
  type        = string
  default     = "Standard_B1s"
}

variable "admin_username" {
  description = "Administrator username for the Linux VMs"
  type        = string
  default     = "azureadmin"
}

variable "admin_password" {
  description = "Administrator password for the Linux VMs (use a strong password!)"
  type        = string
  sensitive   = true
}

# ---- Tags ----

variable "common_tags" {
  description = "Common tags applied to every resource for organization"
  type        = map(string)
  default     = {}
}
