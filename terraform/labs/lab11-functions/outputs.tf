output "slug" {
  description = "Result of lower() and replace()."
  value       = local.slug
}

output "unique_cidrs" {
  description = "Result of toset(), tolist() and sort()."
  value       = local.unique_cidrs
}

output "cidr_count" {
  description = "Result of length()."
  value       = local.cidr_count
}

output "subnet_prefix" {
  description = "Result of cidrsubnet()."
  value       = local.subnet_prefix
}

output "config_json" {
  description = "Result of jsonencode()."
  value       = local.config_json
}

output "summary" {
  description = "Result of format()."
  value       = local.summary
}
