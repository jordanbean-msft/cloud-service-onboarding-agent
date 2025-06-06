module "naming" {
  source  = "Azure/naming/azurerm"
  version = ">= 0.3.0"
  suffix  = var.name_suffix
}

module "avm-res-storage-storageaccount" {
  source              = "Azure/avm-res-storage-storageaccount/azurerm"
  version             = "0.6.3"
  name                = module.naming.storage_account.name
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
  account_tier        = var.account_tier
  diagnostic_settings_blob = {
    workspace_resource_id = var.log_analytics_workspace_id
  }
  diagnostic_settings_file = {
    workspace_resource_id = var.log_analytics_workspace_id
  }
  diagnostic_settings_queue = {
    workspace_resource_id = var.log_analytics_workspace_id
  }
  diagnostic_settings_storage_account = {
    workspace_resource_id = var.log_analytics_workspace_id
  }
  diagnostic_settings_table = {
    workspace_resource_id = var.log_analytics_workspace_id
  }
  network_rules = {
    default_action = "Deny"
    bypass         = "AzureServices"
  }
  public_network_access_enabled = var.public_network_access_enabled
  role_assignments = {
    var.user_assigned_identity_principal_id = {
      principal_id     = var.user_assigned_identity_principal_id
      principal_type   = "ServicePrincipal"
      role_assignments = "StorageBlobDataContributor"
    }
    var.principal_id = {
      principal_id     = var.principal_id
      principal_type   = "UserPrincipal"
      role_assignments = "StorageBlobDataContributor"
    }
  }
  private_endpoints = {
    primary = {
      subnet_resource_id = var.private_endpoint_subnet_resource_id
    }
  }
  account_replication_type = var.account_replication_type
}
