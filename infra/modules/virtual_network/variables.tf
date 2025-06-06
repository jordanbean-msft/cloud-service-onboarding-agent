variable "private_endpoint_subnet_resource_id" {
  description = "The resource ID of the subnet where the private endpoint will be created"
  type        = string
}

variable "container_apps_subnet_resource_id" {
  description = "The resource ID of the subnet for Container Apps"
  type        = string
}
