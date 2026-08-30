output "security_group_id" {
  description = "ID of the generated security group."
  value       = aws_security_group.service.id
}

output "ingress_ports" {
  description = "Ports opened by the dynamic block, sorted."
  value       = sort([for rule in values(var.ingress_rules) : tostring(rule.port)])
}
