# 07 — Local State

By default Terraform writes `terraform.tfstate` in the working directory. State maps configuration addresses to real infrastructure and may contain sensitive data. Protect it and never commit it.

Useful inspections: `terraform state list`, `terraform show`, and `terraform state show ADDRESS`. Local state is suitable for an individual lab only; teams need a protected remote backend with locking and access controls.
