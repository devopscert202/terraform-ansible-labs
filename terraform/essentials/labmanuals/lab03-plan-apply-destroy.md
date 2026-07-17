# Lab 03 — Plan, Apply, and Destroy

**Course alignment:** L8 AP-07  
**Objective:** Practice the Terraform lifecycle safely using only the Random provider.

## Prerequisites

- Terraform 1.5+ installed (`terraform version`).
- For AWS labs, authenticate through `AWS_PROFILE` or an IAM role; credentials must not be placed in `.tf` files.
- Work from `../labs/lab03-plan-apply-destroy`.

## Procedure

### 1. In `labs/lab03-plan-apply-destroy`, run `terraform init` and verify provider installation succeeds.

In `labs/lab03-plan-apply-destroy`, run `terraform init` and verify provider installation succeeds.

**Validate:** Check the stated result before continuing.

### 2. Run `terraform validate`

Run `terraform validate`; verify the configuration is valid.

**Validate:** Check the stated result before continuing.

### 3. Create a reviewed plan: `terraform plan -out=tfplan`

Create a reviewed plan: `terraform plan -out=tfplan`; verify one random string will be added.

**Validate:** Check the stated result before continuing.

### 4. Apply exactly that plan: `terraform apply tfplan`

Apply exactly that plan: `terraform apply tfplan`; verify the `generated_value` output appears.

**Validate:** Check the stated result before continuing.

### 5. Inspect managed objects: `terraform state list`

Inspect managed objects: `terraform state list`; verify `random_string.example` is present.

**Validate:** Check the stated result before continuing.

### 6. Run `terraform destroy`

Run `terraform destroy`; type `yes` and verify the state list is empty.

**Validate:** Check the stated result before continuing.

## Cleanup and evidence

For AWS labs, destruction is mandatory after verification. Record the Terraform version, the reviewed plan summary, and the final destroy result. Do not retain state files or tfvars files containing sensitive data in source control.
