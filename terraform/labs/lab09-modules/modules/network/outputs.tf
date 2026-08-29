# These are the module's outputs. Only these values are visible to the caller.
output "vpc_id" {
  description = "ID of the created VPC."
  value       = aws_vpc.this.id
}

output "subnet_id" {
  description = "ID of the created subnet."
  value       = aws_subnet.this.id
}
