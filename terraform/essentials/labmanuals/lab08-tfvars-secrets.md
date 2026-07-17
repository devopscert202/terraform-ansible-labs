# Lab 08 — tfvars, Validation, and Secrets

**Course alignment:** L10 AP-03  
**Objective:** Pass non-secret values from a tfvars file, validate input values, and provide a sensitive value through the environment.

## Prerequisites

- Terraform 1.5+ installed (`terraform version`).
- For AWS labs, authenticate through `AWS_PROFILE` or an IAM role; credentials must not be placed in `.tf` files.
- Work from `../labs/lab08-tfvars-secrets`.

## Procedure

### 1. In `labs/lab08-tfvars-secrets`, copy the safe example: `cp terraform.tfvars.example terraform.tfvars`.

In `labs/lab08-tfvars-secrets`, copy the safe example: `cp terraform.tfvars.example terraform.tfvars`.

**Validate:** Confirm the command exits with status 0 and the expected result is visible.

### 2. Set an example secret without writing it to a file: `export TF_VAR_phone_number="example-only"`.

Set an example secret without writing it to a file: `export TF_VAR_phone_number="example-only"`.

**Validate:** Confirm the command exits with status 0 and the expected result is visible.

### 3. Run `terraform init && terraform validate`

Run `terraform init && terraform validate`; verify validation succeeds.

**Validate:** Check the stated result before continuing.

### 4. Run `terraform plan`

Run `terraform plan`; verify the public configuration values are shown and the phone value is redacted.

**Validate:** Check the stated result before continuing.

### 5. Run `terraform apply -auto-approve`, then `terraform output`

Run `terraform apply -auto-approve`, then `terraform output`; verify `phone_number` remains sensitive.

**Validate:** Check the stated result before continuing.

### 6. Run `terraform destroy -auto-approve`

Run `terraform destroy -auto-approve`; remove the local `terraform.tfvars` if it contains anything non-public and never commit it.

**Validate:** Confirm the command exits with status 0 and the expected result is visible.

## Cleanup and evidence

For AWS labs, destruction is mandatory after verification. Record the Terraform version, the reviewed plan summary, and the final destroy result. Do not retain state files or tfvars files containing sensitive data in source control.
