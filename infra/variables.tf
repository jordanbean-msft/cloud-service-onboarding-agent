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

variable "principal_id" {
  description = "The principal ID of the user to assign roles to"
  type        = string
}

variable "cosmos_db" {
  description = "Configuration for the Cosmos DB account"
  type = object({
    document_time_to_live = number,
    max_throughput        = number,
    zone_redundant        = bool,
  })
}

variable "storage_account" {
  description = "Configuration for the Storage Account"
  type = object({
    account_tier             = string,
    account_replication_type = string,
  })
}

variable "container_apps" {
  description = "Configuration for the Container Apps"
  type = object({
    frontend = object({
      name     = string,
      template = any
    }),
    backend = object({
      name     = string,
      template = any
    })
  })
}
