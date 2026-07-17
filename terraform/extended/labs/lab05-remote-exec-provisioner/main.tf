terraform {
  required_version = ">= 1.5.0"
}

variable "host" {
  type        = string
  description = "Reachable SSH host. Supply with TF_VAR_host or terraform.tfvars."
}
variable "user" {
  type    = string
  default = "ec2-user"
}
variable "private_key_path" {
  type        = string
  sensitive   = true
  description = "Path to an SSH private key; do not commit it."
}

resource "terraform_data" "bootstrap" {
  input = var.host
  connection {
    type        = "ssh"
    host        = var.host
    user        = var.user
    private_key = file(pathexpand(var.private_key_path))
  }
  provisioner "remote-exec" {
    inline = ["echo Terraform remote-exec connected to $(hostname)"]
  }
}

output "target" {
  value = terraform_data.bootstrap.output
}
