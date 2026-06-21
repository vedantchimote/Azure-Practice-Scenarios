# =============================================================================
# Local Values
# =============================================================================
# Computed values and naming conventions used throughout the configuration.

locals {
  # Standardized resource naming: <project>-<environment>-<resource_type>
  name_prefix = "${var.project_name}-${var.environment}"

  # Merge user-supplied tags with auto-generated ones
  tags = merge(var.common_tags, {
    Project     = var.project_name
    Environment = var.environment
  })
}
