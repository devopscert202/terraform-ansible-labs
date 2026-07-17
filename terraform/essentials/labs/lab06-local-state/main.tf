terraform {
  required_version = ">= 1.5.0"
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# No backend block means Terraform uses local terraform.tfstate.
resource "random_pet" "first" {
  prefix = "state-lab"
  length = 2
}

output "first_resource" {
  value = random_pet.first.id
}
