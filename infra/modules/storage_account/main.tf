module "naming" {
  source  = "Azure/naming/azurerm"
  version = ">= 0.3.0"
  suffix  = [var.name_suffix]
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
    default = {
      workspace_resource_id = var.log_analytics_workspace_resource_id
    }
  }
  diagnostic_settings_file = {
    default = {
      workspace_resource_id = var.log_analytics_workspace_resource_id
    }
  }
  diagnostic_settings_queue = {
    default = {
      workspace_resource_id = var.log_analytics_workspace_resource_id
    }
  }
  diagnostic_settings_storage_account = {
    default = {
      workspace_resource_id = var.log_analytics_workspace_resource_id
    }
  }
  diagnostic_settings_table = {
    default = {
      workspace_resource_id = var.log_analytics_workspace_resource_id
    }
  }
  network_rules = {
    default_action = "Deny"
    bypass         = ["AzureServices"]
  }
  public_network_access_enabled = var.public_network_access_enabled
  role_assignments = {
    user_assigned_managed_identity = {
      principal_id               = var.user_assigned_identity_principal_id
      principal_type             = "ServicePrincipal"
      role_definition_id_or_name = "StorageBlobDataContributor"
    }
  }
  private_endpoints = {
    blob = {
      subnet_resource_id = var.private_endpoint_subnet_resource_id
      subresource_name   = "blob"
    }
    file = {
      subnet_resource_id = var.private_endpoint_subnet_resource_id
      subresource_name   = "file"
    }
    queue = {
      subnet_resource_id = var.private_endpoint_subnet_resource_id
      subresource_name   = "queue"
    }
    table = {
      subnet_resource_id = var.private_endpoint_subnet_resource_id
      subresource_name   = "table"
    }
  }
  account_replication_type = var.account_replication_type
}
