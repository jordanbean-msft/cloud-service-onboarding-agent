module "naming" {
  source  = "Azure/naming/azurerm"
  version = ">= 0.3.0"
  suffix  = [var.name_suffix]
}

module "avm-res-cognitiveservices-account" {
  source                        = "Azure/avm-res-cognitiveservices-account/azurerm"
  version                       = "0.7.1"
  kind                          = "Bing.CustomSearch"
  location                      = "global"
  name                          = "Bing-${module.naming.cognitive_account.name}"
  sku_name                      = "G2"
  tags                          = var.tags
  resource_group_name           = var.resource_group_name
  public_network_access_enabled = var.public_network_access_enabled
  private_endpoints = {
    primary = {
      subnet_resource_id = var.private_endpoint_subnet_resource_id
    }
  }
  diagnostic_settings = {
    default = {
      workspace_resource_id = var.log_analytics_workspace_resource_id
    }
  }
  # role_assignments = {
  #   user_assigned_identity_id = {
  #     principal_id               = var.user_assigned_identity_principal_id
  #     principal_type             = "ServicePrincipal"
  #     role_definition_id_or_name = "Cognitive Services Account User"
  #   }
  # }
  # network_acls = {
  #   bypass         = "AzureServices"
  #   default_action = "Deny"
  # }
  custom_subdomain_name = "Bing-${module.naming.cognitive_account.name}"
}
