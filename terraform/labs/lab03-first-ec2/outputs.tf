output "instance_id" {
  description = "The id AWS assigned to the new instance."
  value       = aws_instance.web.id
}

output "public_ip" {
  description = "Public IP address, empty if the subnet does not assign one."
  value       = aws_instance.web.public_ip
}

output "ami_id" {
  description = "The Amazon Linux 2023 image the data source resolved to."
  value       = data.aws_ami.amazon_linux.id
}
