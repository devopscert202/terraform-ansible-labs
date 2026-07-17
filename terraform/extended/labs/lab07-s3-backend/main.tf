terraform {
  required_version = ">= 1.5.0"
  backend "s3" {}
}

resource "terraform_data" "state_owner" { input = "shared-state" }
output "state_owner" { value = terraform_data.state_owner.output }
