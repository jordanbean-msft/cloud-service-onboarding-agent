# Configure the Azure Provider
terraform {
  required_version = ">= 1.1.7, < 2.0.0"
  backend "azurerm" {
  }
}

# Make client_id, tenant_id, subscription_id and object_id variables
data "azurerm_client_config" "current" {}
