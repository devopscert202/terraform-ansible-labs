output "server_name" {
  description = "Generated pet name for the pretend server."
  value       = random_pet.server.id
}

output "db_password" {
  description = "Generated secret. Redacted on screen, plain text in state."
  value       = random_password.db.result
  sensitive   = true
}
