output "private_endpoint_subnet_resource_id" {
  description = "The resource ID of the subnet for the private endpoint"
  value       = var.private_endpoint_subnet_resource_id
}

output "container_apps_subnet_resource_id" {
  description = "The resource ID of the subnet for the Container Apps"
  value       = var.container_apps_subnet_resource_id
}
