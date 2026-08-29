terraform {
  # Higher than the track's >= 1.5.0 floor: backend.hcl.example sets use_lockfile,
  # which is experimental in 1.10 and generally available from 1.11.
  required_version = ">= 1.11.0"

  # Step 6 of the lab manual has you add the S3 backend block here:
  #   backend "s3" {}
}

resource "terraform_data" "migrated_state" { input = "migrate with terraform init -migrate-state" }
output "migration_instruction" { value = terraform_data.migrated_state.output }
