module "avm-res-app-containerapp" {
  source                                = "Azure/avm-res-app-containerapp/azurerm"
  version                               = "0.6.0"
  name                                  = var.name
  resource_group_name                   = var.resource_group_name
  tags                                  = var.tags
  revision_mode                         = "Single"
  container_app_environment_resource_id = var.container_app_environment_resource_id
  template                              = var.template
  managed_identities = {
    user_assigned_resource_ids = [var.user_assigned_identity_resource_id]
  }
  registries = {
    server   = var.container_registry_hostname
    identity = var.user_assigned_identity_resource_id
  }
}
