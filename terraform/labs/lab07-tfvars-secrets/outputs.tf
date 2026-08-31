output "settings" {
  description = "Non-secret values, safe to print."
  value       = local.settings
}

output "db_password" {
  description = "Marked sensitive, so the CLI prints (sensitive value) instead of the password."
  value       = var.db_password
  sensitive   = true
}

output "db_password_length" {
  description = "Proof the password arrived, without revealing it. nonsensitive() unmarks the value."
  value       = nonsensitive(length(var.db_password))
}

output "vpc_id" {
  description = "The real VPC the tfvars values were applied to."
  value       = aws_vpc.main.id
}

output "vpc_tags" {
  description = "The tags AWS recorded, read back off the VPC. Every value came from terraform.tfvars."
  value       = aws_vpc.main.tags_all
}

output "subnet_id" {
  description = "The real subnet, tagged from the same tfvars values."
  value       = aws_subnet.main.id
}
