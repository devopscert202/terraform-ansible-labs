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
