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
