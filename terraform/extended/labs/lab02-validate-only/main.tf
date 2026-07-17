terraform { required_version = ">= 1.5.0" }

locals { course = "terraform-extended" }
resource "terraform_data" "validation_probe" { input = local.course }
output "validation_probe" { value = terraform_data.validation_probe.output }
