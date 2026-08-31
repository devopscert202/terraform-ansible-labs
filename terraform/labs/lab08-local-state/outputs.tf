output "server_name" {
  description = "Generated pet name for the pretend server."
  value       = random_pet.server.id
}

output "db_password" {
  description = "Generated secret. Redacted on screen, plain text in state."
  value       = random_password.db.result
  sensitive   = true
}

output "vpc_id" {
  description = "The real VPC ID AWS assigned. State is the only local record that this exists."
  value       = aws_vpc.main.id
}
