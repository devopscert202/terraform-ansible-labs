# Root outputs re-export the child module's outputs so the CLI can show them.
output "vpc_id" {
  description = "ID of the VPC created by the network module."
  value       = module.network.vpc_id
}

output "subnet_id" {
  description = "ID of the subnet created by the network module."
  value       = module.network.subnet_id
}
