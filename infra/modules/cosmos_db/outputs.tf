output "cosmos_db_account_id" {
  description = "The ID of the Cosmos DB account"
  value       = module.avm-res-cosmosdb-account.id
}

output "cosmos_db_account_name" {
  description = "The name of the Cosmos DB account"
  value       = module.avm-res-cosmosdb-account.name
}
