terraform {
  required_version = ">= 1.5.0"
}

variable "network_state_path" {
  type    = string
  default = "../lab08-state-keys/terraform.tfstate"
}

data "terraform_remote_state" "network" {
  backend = "local"
  config = {
    path = var.network_state_path
  }
}

output "upstream_outputs" {
  value = data.terraform_remote_state.network.outputs
}
