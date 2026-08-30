output "instance_id" {
  description = "EC2 instance ID."
  value       = aws_instance.web.id
}

output "instance_arn" {
  description = "Full Amazon Resource Name of the instance."
  value       = aws_instance.web.arn
}

output "public_ip" {
  description = "Public IPv4 address assigned to the instance."
  value       = aws_instance.web.public_ip
}

output "applied_tags" {
  description = "The merged tag map that was applied to the instance."
  value       = local.common_tags
}

output "list_vs_set" {
  description = "Element counts proving a set drops the duplicate the list keeps."
  value       = local.list_vs_set
}

output "profile_department" {
  description = "Value of the optional() object attribute that the default never sets."
  value       = var.server_profile.department
}

output "release_build" {
  description = "Position 1 of the tuple, still a number after being stored beside a string."
  value       = var.release_marker[1]
}

output "prod_instance_type" {
  description = "One attribute reached through a map(object(...)) key."
  value       = var.environments["prod"].instance_type
}

output "total_disk_gb" {
  description = "Root volume plus every extra disk, summed as numbers."
  value       = local.total_disk_gb
}

output "freeform" {
  description = "Value of the any-typed variable, returned with whatever shape it was given."
  value       = var.freeform
}

output "contact" {
  description = "Fallback applied because owner_email is null."
  value       = local.contact
}

output "owner_email_state" {
  description = "Distinguishes an unset (null) owner_email from one set to an empty string."
  value       = local.owner_email_state
}

output "api_token" {
  description = "Redacted because the variable is sensitive."
  value       = var.api_token
  sensitive   = true
}

output "vpc_id" {
  description = "ID of the VPC this lab creates."
  value       = aws_vpc.main.id
}

output "subnet_id" {
  description = "ID of the subnet the instance launched into."
  value       = aws_subnet.main.id
}

output "security_group_id" {
  description = "ID of the security group attached to the instance."
  value       = aws_security_group.instance.id
}
