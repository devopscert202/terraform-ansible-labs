output "vpc_id" {
  description = "Id of the VPC this lab created."
  value       = aws_vpc.main.id
}

output "public_subnet_id" {
  description = "Id of the subnet the instance launched into."
  value       = aws_subnet.public.id
}

output "private_subnet_id" {
  description = "Id of the second subnet."
  value       = aws_subnet.private.id
}

output "public_subnet_az" {
  description = "Availability zone the public subnet was placed in."
  value       = aws_subnet.public.availability_zone
}

output "private_subnet_az" {
  description = "Availability zone the private subnet was placed in."
  value       = aws_subnet.private.availability_zone
}

output "security_group_id" {
  description = "Id of the security group attached to the instance."
  value       = aws_security_group.instance.id
}

output "instance_id" {
  description = "Id AWS assigned to the new instance."
  value       = aws_instance.web.id
}

# There is no public_ip output: the subnet has no internet gateway and the
# instance is not assigned a public address.
output "instance_private_ip" {
  description = "Private IP the instance holds inside the VPC."
  value       = aws_instance.web.private_ip
}
