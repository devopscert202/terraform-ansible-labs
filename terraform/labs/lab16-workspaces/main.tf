terraform { required_version = ">= 1.5.0" }

locals {
  environment = terraform.workspace
  labels      = { environment = terraform.workspace, managed_by = "terraform" }
}

resource "terraform_data" "workspace" { input = local.labels }
output "workspace" { value = terraform.workspace }
output "labels" { value = terraform_data.workspace.output }
