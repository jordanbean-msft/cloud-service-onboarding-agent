module "naming" {
  source  = "Azure/naming/azurerm"
  version = ">= 0.3.0"
  suffix  = [var.name_suffix]
}

module "avm-res-search-searchservice" {
  source              = "Azure/avm-res-search-searchservice/azurerm"
  version             = "0.1.5"
  name                = module.naming.user_assigned_identity.name
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
  private_endpoints = {
    primary = {
      subnet_resource_id = var.private_endpoint_subnet_resource_id
    }
  }
  public_network_access_enabled = var.public_network_access_enabled
  diagnostic_settings = {
    default = {
      workspace_resource_id = var.log_analytics_workspace_resource_id
    }
  }
  sku = "standard"
  role_assignments = {
    user_assigned_managed_identity = {
      principal_id               = var.user_assigned_identity_principal_id
      principal_type             = "ServicePrincipal"
      role_definition_id_or_name = "Search Index Data Contributor"
    }
  }
  local_authentication_enabled = false
}
