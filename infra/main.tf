locals {
  tags           = { azd-env-name : var.environment_name }
  sha            = base64encode(sha256("${var.location}${data.azurerm_client_config.current.subscription_id}${var.resource_group_name}"))
  resource_token = substr(replace(lower(local.sha), "[^A-Za-z0-9_]", ""), 0, 13)
}

data "azurerm_subnet" "private_endpoint_subnet" {
  name                 = var.network.private_endpoint_subnet_name
  virtual_network_name = var.network.virtual_network_name
  resource_group_name  = var.resource_group_name
}

data "azurerm_subnet" "container_apps_subnet" {
  name                 = var.network.container_apps_subnet_name
  virtual_network_name = var.network.virtual_network_name
  resource_group_name  = var.resource_group_name
}

data "azurerm_subnet" "ai_foundry_agent_subnet" {
  name                 = var.network.ai_foundry_agent_subnet_name
  virtual_network_name = var.network.virtual_network_name
  resource_group_name  = var.resource_group_name
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
  source                = "./modules/app_insights"
  name_suffix           = local.resource_token
  location              = var.location
  resource_group_name   = var.resource_group_name
  workspace_resource_id = module.log_analytics_workspace.log_analytics_workspace_resource_id
  tags                  = local.tags
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
  log_analytics_workspace_resource_id = module.log_analytics_workspace.log_analytics_workspace_resource_id
  public_network_access_enabled       = var.public_network_access_enabled
  private_endpoint_subnet_resource_id = module.virtual_network.private_endpoint_subnet_resource_id
  user_assigned_identity_principal_id = module.managed_identity.user_assigned_identity_principal_id
  zone_redundancy_enabled             = var.zone_redundancy_enabled
}

# ------------------------------------------------------------------------------------------------------
# Deploy Storage Account
# ------------------------------------------------------------------------------------------------------

module "storage_account" {
  source                              = "./modules/storage_account"
  name_suffix                         = local.resource_token
  location                            = var.location
  resource_group_name                 = var.resource_group_name
  log_analytics_workspace_resource_id = module.log_analytics_workspace.log_analytics_workspace_resource_id
  public_network_access_enabled       = var.public_network_access_enabled
  private_endpoint_subnet_resource_id = module.virtual_network.private_endpoint_subnet_resource_id
  user_assigned_identity_principal_id = module.managed_identity.user_assigned_identity_principal_id
  account_tier                        = var.storage_account.account_tier
  account_replication_type            = var.storage_account.account_replication_type
}

# ------------------------------------------------------------------------------------------------------
# Deploy Virtual Network
# ------------------------------------------------------------------------------------------------------

module "virtual_network" {
  source                              = "./modules/virtual_network"
  container_apps_subnet_resource_id   = data.azurerm_subnet.container_apps_subnet.id
  private_endpoint_subnet_resource_id = data.azurerm_subnet.private_endpoint_subnet.id
  ai_foundry_agent_subnet_resource_id = data.azurerm_subnet.ai_foundry_agent_subnet.id
}

# ------------------------------------------------------------------------------------------------------
# Deploy Container Apps Environment
# ------------------------------------------------------------------------------------------------------

module "container_apps_environment" {
  source                                     = "./modules/container_apps_environment"
  name_suffix                                = local.resource_token
  location                                   = var.location
  resource_group_name                        = var.resource_group_name
  log_analytics_workspace_resource_id        = module.log_analytics_workspace.log_analytics_workspace_resource_id
  log_analytics_workspace_customer_id        = module.log_analytics_workspace.log_analytics_workspace_customer_id
  log_analytics_workspace_primary_shared_key = module.log_analytics_workspace.log_analytics_workspace_primary_shared_key
  public_network_access_enabled              = var.public_network_access_enabled
  container_apps_subnet_resource_id          = module.virtual_network.container_apps_subnet_resource_id
  user_assigned_identity_principal_id        = module.managed_identity.user_assigned_identity_principal_id
}

# ------------------------------------------------------------------------------------------------------
# Deploy Container Apps - Frontend
# ------------------------------------------------------------------------------------------------------

module "container_apps_frontend" {
  source                                 = "./modules/container_apps"
  name                                   = var.container_apps.frontend.name
  location                               = var.location
  resource_group_name                    = var.resource_group_name
  public_network_access_enabled          = var.public_network_access_enabled
  user_assigned_identity_resource_id     = module.managed_identity.user_assigned_identity_id
  container_apps_environment_resource_id = module.container_apps_environment.container_apps_environment_id
  container_registry_hostname            = module.container_registry.container_registry_login_server
  ingress                                = var.container_apps.frontend.ingress
  scale                                  = var.container_apps.frontend.scale
  containers                             = var.container_apps.frontend.containers
}

# ------------------------------------------------------------------------------------------------------
# Deploy Container Apps - Backend
# ------------------------------------------------------------------------------------------------------

module "container_apps_backend" {
  source                                 = "./modules/container_apps"
  name                                   = var.container_apps.backend.name
  location                               = var.location
  resource_group_name                    = var.resource_group_name
  public_network_access_enabled          = var.public_network_access_enabled
  user_assigned_identity_resource_id     = module.managed_identity.user_assigned_identity_id
  container_apps_environment_resource_id = module.container_apps_environment.container_apps_environment_id
  container_registry_hostname            = module.container_registry.container_registry_login_server
  ingress                                = var.container_apps.backend.ingress
  scale                                  = var.container_apps.backend.scale
  containers                             = var.container_apps.backend.containers
}

# ------------------------------------------------------------------------------------------------------
# Deploy Cosmos DB
# ------------------------------------------------------------------------------------------------------

module "cosmos_db" {
  source                              = "./modules/cosmos_db"
  name_suffix                         = local.resource_token
  location                            = var.location
  resource_group_name                 = var.resource_group_name
  log_analytics_workspace_resource_id = module.log_analytics_workspace.log_analytics_workspace_resource_id
  public_network_access_enabled       = var.public_network_access_enabled
  private_endpoint_subnet_resource_id = module.virtual_network.private_endpoint_subnet_resource_id
  user_assigned_identity_principal_id = module.managed_identity.user_assigned_identity_principal_id
  document_time_to_live               = var.cosmos_db.document_time_to_live
  max_throughput                      = var.cosmos_db.max_throughput
  zone_redundancy_enabled             = var.zone_redundancy_enabled
  subscription_id                     = data.azurerm_client_config.current.subscription_id
}

# ------------------------------------------------------------------------------------------------------
# Deploy Bing Custom Search
# ------------------------------------------------------------------------------------------------------

# module "bing_custom_search" {
#   source                              = "./modules/bing_custom_search"
#   name_suffix                         = local.resource_token
#   location                            = var.location
#   resource_group_name                 = var.resource_group_name
#   log_analytics_workspace_resource_id = module.log_analytics_workspace.log_analytics_workspace_resource_id
#   public_network_access_enabled       = var.public_network_access_enabled
#   private_endpoint_subnet_resource_id = module.virtual_network.private_endpoint_subnet_resource_id
#   user_assigned_identity_principal_id = module.managed_identity.user_assigned_identity_principal_id
# }

# ------------------------------------------------------------------------------------------------------
# Deploy AI Search
# ------------------------------------------------------------------------------------------------------

module "ai_search" {
  source                              = "./modules/ai_search"
  name_suffix                         = local.resource_token
  location                            = var.location
  resource_group_name                 = var.resource_group_name
  log_analytics_workspace_resource_id = module.log_analytics_workspace.log_analytics_workspace_resource_id
  public_network_access_enabled       = var.public_network_access_enabled
  private_endpoint_subnet_resource_id = module.virtual_network.private_endpoint_subnet_resource_id
  user_assigned_identity_principal_id = module.managed_identity.user_assigned_identity_principal_id
}

# -------------------------------------------------------------------------------------------------------
# Deploy AI Foundry
# -------------------------------------------------------------------------------------------------------

module "ai_foundry" {
  source                                = "./modules/ai_foundry"
  name_suffix                           = local.resource_token
  location                              = var.location
  resource_group_name                   = var.resource_group_name
  log_analytics_workspace_resource_id   = module.log_analytics_workspace.log_analytics_workspace_resource_id
  public_network_access_enabled         = var.public_network_access_enabled
  private_endpoint_subnet_resource_id   = module.virtual_network.private_endpoint_subnet_resource_id
  user_assigned_identity_id             = module.managed_identity.user_assigned_identity_id
  storage_account_resource_id           = module.storage_account.storage_account_id
  storage_account_primary_blob_endpoint = module.storage_account.storage_account_primary_blob_endpoint
  cosmos_db_account_resource_id         = module.cosmos_db.cosmos_db_account_id
  ai_search_resource_id                 = module.ai_search.ai_search_id
  ai_search_name                        = module.ai_search.ai_search_name
  cosmos_db_account_document_endpoint   = module.cosmos_db.cosmos_db_account_document_endpoint
  ai_foundry_agent_subnet_resource_id   = module.virtual_network.ai_foundry_agent_subnet_resource_id
}
