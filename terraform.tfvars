# =============================================================================
# Variable Overrides
# =============================================================================
# Customize these values for your deployment.
# IMPORTANT: Never commit this file if it contains secrets. Add to .gitignore!

project_name = "webdemo"
environment  = "dev"
location     = "Central India"

vm_count = 2
vm_size  = "Standard_B1s"

admin_username = "azureadmin"
admin_password = "P@ssw0rd2026!"   # <-- CHANGE THIS to a strong password

common_tags = {
  Project     = "Azure-Learning"
  Environment = "dev"
  ManagedBy   = "Terraform"
}
