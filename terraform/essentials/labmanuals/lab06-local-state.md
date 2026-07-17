# Lab 06 — Local State

**Course alignment:** L9 AP-01  
**Objective:** Inspect the default local backend and see how state records a managed resource.

## Prerequisites

- Terraform 1.5+ installed (`terraform version`).
- For AWS labs, authenticate through `AWS_PROFILE` or an IAM role; credentials must not be placed in `.tf` files.
- Work from `../labs/lab06-local-state`.

## Procedure

### 1. In `labs/lab06-local-state`, run `terraform init && terraform apply -auto-approve`

In `labs/lab06-local-state`, run `terraform init && terraform apply -auto-approve`; verify `random_pet.first` is created.

**Validate:** Check the stated result before continuing.

### 2. Run `terraform state list`

Run `terraform state list`; verify `random_pet.first` is listed.

**Validate:** Check the stated result before continuing.

### 3. Run `terraform show`

Run `terraform show`; verify its generated ID matches the output.

**Validate:** Check the stated result before continuing.

### 4. Confirm `terraform.tfstate` exists in the current lab directory. Treat it as sensitive operational data and do not commit it.

Confirm `terraform.tfstate` exists in the current lab directory. Treat it as sensitive operational data and do not commit it.

**Validate:** Confirm the command exits with status 0 and the expected result is visible.

### 5. Run `terraform destroy -auto-approve`

Run `terraform destroy -auto-approve`; verify destruction completes, then run `terraform state list` and verify no resources remain.

**Validate:** Check the stated result before continuing.

## Cleanup and evidence

For AWS labs, destruction is mandatory after verification. Record the Terraform version, the reviewed plan summary, and the final destroy result. Do not retain state files or tfvars files containing sensitive data in source control.
