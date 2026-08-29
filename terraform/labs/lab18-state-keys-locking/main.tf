terraform {
  # Higher than the track's >= 1.5.0 floor: backend.hcl.example sets use_lockfile,
  # which is experimental in 1.10 and generally available from 1.11.
  required_version = ">= 1.11.0"
  backend "s3" {}
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Environment segment of the state key, e.g. dev or staging."
}

variable "component" {
  type        = string
  default     = "network"
  description = "Component segment of the state key, e.g. network or app."
}

locals {
  recommended_key = "labs/${var.environment}/${var.component}/terraform.tfstate"
}

resource "terraform_data" "key_design" {
  input = local.recommended_key
}

resource "terraform_data" "locking_note" {
  input = "S3 lockfiles prevent concurrent state writes."
}

output "recommended_state_key" {
  value = terraform_data.key_design.output
}

output "locking_note" {
  value = terraform_data.locking_note.output
}
