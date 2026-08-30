output "vpc_id" {
  description = "ID of the VPC created by this capstone."
  value       = aws_vpc.this.id
}

output "public_ip" {
  description = "Public IPv4 address assigned to the web server."
  value       = aws_instance.web.public_ip
}

output "web_url" {
  description = "Full URL of the web server. Open it or curl it to verify the build."
  value       = "http://${aws_instance.web.public_ip}"
}
