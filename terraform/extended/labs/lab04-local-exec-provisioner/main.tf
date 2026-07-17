terraform {
  required_version = ">= 1.5.0"
}

variable "message" {
  type    = string
  default = "local-exec completed"
}

resource "terraform_data" "local_action" {
  input = var.message
  provisioner "local-exec" {
    command = "printf '%s\n' '${self.input}'"
  }
}

output "message" {
  value = terraform_data.local_action.output
}
