terraform {
  required_version = ">= 1.5.0"
  backend "s3" {}
}

resource "terraform_data" "migrated_state" { input = "migrate with terraform init -migrate-state" }
output "migration_instruction" { value = terraform_data.migrated_state.output }
