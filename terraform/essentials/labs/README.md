# Terraform Essentials Lab Configurations

**Directories:** `lab01-providers-init`, `lab02-ec2`, `lab03-plan-apply-destroy`, `lab04-fmt-validate`, `lab05-variables`, `lab06-local-state`, `lab07-simple-module`, `lab08-tfvars-secrets`.

Each directory is an independent Terraform root module. Initialize, validate, plan, apply, and destroy it independently. AWS examples read credentials from the standard AWS chain; set `AWS_PROFILE` or use an IAM role before planning.

`lab03`, `lab04`, `lab06`, and `lab08` need no AWS account. The remaining labs create AWS resources and must be cleaned up with `terraform destroy`.
