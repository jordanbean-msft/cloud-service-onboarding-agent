terraform {
  required_version = "~> 1.9"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.7.0, < 5.0.0"
    }
    azapi = {
      source  = "Azure/azapi"
      version = "2.4.0"
    }
  }
}

provider "azurerm" {
  features {
  }
}
