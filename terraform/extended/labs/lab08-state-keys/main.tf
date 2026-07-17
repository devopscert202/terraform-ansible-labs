terraform {
  required_version = ">= 1.5.0"
  backend "s3" {}
}

variable "environment" {
  type    = string
  default = "dev"
}

locals {
  recommended_key = "extended/${var.environment}/network/terraform.tfstate"
}

resource "terraform_data" "key_design" {
  input = local.recommended_key
}

output "recommended_state_key" {
  value = terraform_data.key_design.output
}
