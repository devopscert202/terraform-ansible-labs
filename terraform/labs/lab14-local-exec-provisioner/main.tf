terraform {
  required_version = ">= 1.5.0"
}

variable "message" {
  type        = string
  default     = "local-exec completed"
  description = "Text the local-exec provisioner prints on the machine running Terraform."
}

resource "terraform_data" "local_action" {
  input = var.message
  provisioner "local-exec" {
    command = "printf '%s\n' '${self.input}'"
  }
  # Runs before the resource is destroyed instead of after creation.
  # A destroy-time provisioner may reference self, but not var or other resources.
  provisioner "local-exec" {
    when    = destroy
    command = "printf 'destroying %s\n' '${self.input}'"
  }
}

output "message" {
  value = terraform_data.local_action.output
}
