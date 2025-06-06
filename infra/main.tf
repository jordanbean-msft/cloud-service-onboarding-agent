locals {
  tags           = { azd-env-name : var.environment_name }
  sha            = base64encode(sha256("${var.location}${data.azurerm_client_config.current.subscription_id}"))
  resource_token = substr(replace(lower(local.sha), "[^A-Za-z0-9_]", ""), 0, 13)
}

# ------------------------------------------------------------------------------------------------------
# Deploy Log Analytics Workspace
# ------------------------------------------------------------------------------------------------------

module "log_analytics_workspace" {
  source              = "./modules/log_analytics"
  name_suffix         = local.resource_token
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = local.tags
}

# ------------------------------------------------------------------------------------------------------
# Deploy Application Insights
# ------------------------------------------------------------------------------------------------------

module "application_insights" {
  source                     = "./modules/app_insights"
  name_suffix                = local.resource_token
  location                   = var.location
  resource_group_name        = var.resource_group_name
  log_analytics_workspace_id = module.log_analytics_workspace.log_analytics_workspace_id
  tags                       = local.tags
}

# ------------------------------------------------------------------------------------------------------
# Deploy Managed Identity
# ------------------------------------------------------------------------------------------------------

module "managed_identity" {
  source              = "./modules/managed_identity"
  name_suffix         = local.resource_token
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = local.tags
}

# ------------------------------------------------------------------------------------------------------
# Deploy Container Registry
# ------------------------------------------------------------------------------------------------------

module "container_registry" {
  source                              = "./modules/container_registry"
  name_suffix                         = local.resource_token
  location                            = var.location
  resource_group_name                 = var.resource_group_name
  log_analytics_workspace_id          = module.log_analytics_workspace.log_analytics_workspace_id
  public_network_access_enabled       = var.public_network_access_enabled
  private_endpoint_subnet_resource_id = var.private_endpoint_subnet_resource_id
  user_assigned_identity_principal_id = module.managed_identity.user_assigned_identity_principal_id
}
