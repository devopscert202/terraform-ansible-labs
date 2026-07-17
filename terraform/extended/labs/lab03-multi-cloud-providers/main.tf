terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws    = { source = "hashicorp/aws", version = "~> 5.0" }
    random = { source = "hashicorp/random", version = "~> 3.0" }
  }
}

provider "aws" { region = var.aws_region }
provider "random" {}

resource "random_pet" "label" { length = 2 }

output "provider_composition" {
  value = { aws_region = var.aws_region, generated_label = random_pet.label.id }
}
