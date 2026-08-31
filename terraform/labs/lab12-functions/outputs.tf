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

output "vpc_id" {
  description = "The real VPC whose CIDR every network function above was derived from."
  value       = aws_vpc.main.id
}

output "derived_subnet" {
  description = "cidrsubnet() output beside the CIDR AWS actually assigned to the subnet."
  value = {
    computed_by_cidrsubnet = local.subnet_prefix
    assigned_by_aws        = aws_subnet.derived.cidr_block
    subnet_id              = aws_subnet.derived.id
  }
}

output "derived_subnet_gateway_host" {
  description = "cidrhost() applied to the real subnet's CIDR read back from AWS."
  value       = cidrhost(aws_subnet.derived.cidr_block, 1)
}

output "security_group_ingress_cidrs" {
  description = "The deduplicated, sorted CIDR list as AWS recorded it on the security group."
  value       = tolist(aws_security_group.app.ingress)[0].cidr_blocks
}
