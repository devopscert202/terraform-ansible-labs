terraform {
  # Higher than the track's >= 1.5.0 floor: backend.hcl.example sets use_lockfile,
  # which is experimental in 1.10 and generally available from 1.11.
  required_version = ">= 1.11.0"
  backend "s3" {}
}

resource "terraform_data" "state_owner" { input = "shared-state" }
output "state_owner" { value = terraform_data.state_owner.output }
