# =============================================================================
# Azure Provider Configuration
# =============================================================================
# This file configures the Terraform provider for Azure Resource Manager (azurerm).
# The 'features' block is required even if empty.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.100"
    }
  }
}

provider "azurerm" {
  features {}

  # Uncomment and fill these if you are NOT using 'az login' for authentication.
  # subscription_id = var.subscription_id
  # tenant_id       = var.tenant_id
  # client_id       = var.client_id
  # client_secret   = var.client_secret
}
