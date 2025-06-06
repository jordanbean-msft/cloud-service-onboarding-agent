variable "location" {
  description = "The Azure location to deploy the resources"
  type        = string
}

variable "tags" {
  description = "Tags to be applied to all resources"
  type        = map(string)
  default     = {}
}

variable "resource_group_name" {
  description = "The name of the resource group where resources will be created"
  type        = string
}

variable "environment_name" {
  description = "The name of the environment, used for tagging and resource naming"
  type        = string
}

variable "public_network_access_enabled" {
  description = "Enable or disable public network access to the resources"
  type        = bool
}

variable "private_endpoint_subnet_resource_id" {
  description = "The resource ID of the subnet where the private endpoint will be created"
  type        = string
}

variable "container_apps_subnet_resource_id" {
  description = "The resource ID of the subnet for Container Apps"
  type        = string
}
