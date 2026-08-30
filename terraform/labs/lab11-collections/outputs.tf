output "list_has_duplicates" {
  description = "The list keeps both copies of web and keeps its order."
  value       = var.tag_names
}

output "set_removed_duplicates" {
  description = "The set dropped the repeated zone. sort() gives a stable order."
  value       = sort(tolist(var.availability_zones))
}

output "count_addresses" {
  description = "Values produced by count, in index order."
  value       = terraform_data.by_count[*].output
}

output "each_addresses" {
  description = "Values produced by for_each, keyed by map key."
  value       = { for key, item in terraform_data.by_each : key => item.output.cidr }
}
