output "container_apps_id" {
  description = "The ID of the Azure Container Apps"
  value       = module.avm-res-containerapps-app.id
}

output "container_apps_name" {
  description = "The name of the Azure Container Apps"
  value       = module.avm-res-containerapps-app.name
}

output "container_apps_fqdn" {
  description = "The FQDN of the Azure Container Apps"
  value       = module.avm-res-containerapps-app.fqdn
}
