# 02 — Providers and Initialization

A `terraform` block pins compatible Terraform and provider versions. `terraform init` downloads providers and records exact selections in `.terraform.lock.hcl`.

Use `terraform providers` to inspect requirements and `terraform init -upgrade` only when intentionally refreshing compatible provider versions. Provider configuration belongs in the root module; child modules should declare requirements but not configure credentials.
