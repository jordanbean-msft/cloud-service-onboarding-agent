output "log_analytics_workspace_id" {
  value = avm-res-operationalinsights-workspace.resource_id
}

output "log_analytics_workspace_customer_id" {
  value = avm-res-operationalinsights-workspace.resource.workspace_id
}

output "log_analytics_workspace_primary_shared_key" {
  value     = avm-res-operationalinsights-workspace.resource.primary_shared_key
  sensitive = true
}

output "log_analytics_workspace_customer_id" {
  value = avm-res-operationalinsights-workspace.resource.log_analytics_workspace_customer_id
}

