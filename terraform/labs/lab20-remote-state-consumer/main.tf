terraform {
  required_version = ">= 1.5.0"
}

variable "upstream_state_path" {
  type        = string
  description = "Path to the producer lab's state file that this consumer reads."
  default     = "../lab16-workspaces/terraform.tfstate"
}

data "terraform_remote_state" "upstream" {
  backend = "local"
  config = {
    path = var.upstream_state_path
  }
}

output "upstream_outputs" {
  value = data.terraform_remote_state.upstream.outputs
}

output "upstream_environment" {
  value = data.terraform_remote_state.upstream.outputs.labels.environment
}
