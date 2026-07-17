terraform {
  required_version = ">= 1.5.0"
  backend "s3" {}
}

resource "terraform_data" "locking_note" { input = "S3 lockfiles prevent concurrent state writes." }
output "locking_note" { value = terraform_data.locking_note.output }
