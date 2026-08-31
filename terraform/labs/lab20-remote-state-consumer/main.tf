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

# The realistic cross-stack read: an application stack asking the network stack
# for the VPC it should build into. The ID belongs to a real VPC in AWS, but this
# module never contacts AWS — it reads the producer's state file and nothing else.
output "upstream_vpc_id" {
  description = "The producer's real VPC ID, read out of its state file."
  value       = data.terraform_remote_state.upstream.outputs.vpc_id
}

output "upstream_vpc_cidr" {
  description = "The producer's VPC CIDR, the value a consumer would use in a route or rule."
  value       = data.terraform_remote_state.upstream.outputs.vpc_cidr
}
