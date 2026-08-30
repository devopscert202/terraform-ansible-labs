output "list_has_duplicates" {
  description = "The list keeps both copies of web and keeps its order."
  value       = var.tag_names
}

output "set_removed_duplicates" {
  description = "The set dropped the repeated zone. sort() gives a stable order."
  value       = sort(tolist(var.availability_zones))
}

output "unique_tag_names" {
  description = "The list after toset() removed its duplicate."
  value       = local.unique_tag_names
}

output "tag_labels" {
  description = "A for expression over a list. One output element per input element, order preserved."
  value       = local.tag_labels
}

output "subnet_cidrs" {
  description = "A for expression over a map. Keys are kept, values are reduced to one attribute."
  value       = local.subnet_cidrs
}

output "zone_a_subnets" {
  description = "A for expression with an if clause. Only entries in us-east-2a survive."
  value       = local.zone_a_subnets
}

output "collection_shapes" {
  description = "Lengths, keys, and one addressed element from each collection type, read back out of state."
  value       = terraform_data.collections.output
}
