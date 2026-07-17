# Lab 04 — Format and Validate

**Course alignment:** L8 AP-05  
**Objective:** Use formatting and static validation as fast quality checks before a plan.

## Prerequisites

- Terraform 1.5+ installed (`terraform version`).
- For AWS labs, authenticate through `AWS_PROFILE` or an IAM role; credentials must not be placed in `.tf` files.
- Work from `../labs/lab04-fmt-validate`.

## Procedure

### 1. In `labs/lab04-fmt-validate`, run `terraform init`

In `labs/lab04-fmt-validate`, run `terraform init`; verify the Random provider initializes.

**Validate:** Check the stated result before continuing.

### 2. Run `terraform fmt -check`

Run `terraform fmt -check`; it should exit successfully on the supplied formatted files.

**Validate:** Confirm the command exits with status 0 and the expected result is visible.

### 3. Run `terraform fmt -recursive` and then `git diff --check`

Run `terraform fmt -recursive` and then `git diff --check`; verify no whitespace errors are reported.

**Validate:** Check the stated result before continuing.

### 4. Run `terraform validate`

Run `terraform validate`; verify the configuration is valid.

**Validate:** Check the stated result before continuing.

### 5. Optionally run `terraform plan`

Optionally run `terraform plan`; verify the output value is marked sensitive.

**Validate:** Check the stated result before continuing.

## Cleanup and evidence

For AWS labs, destruction is mandatory after verification. Record the Terraform version, the reviewed plan summary, and the final destroy result. Do not retain state files or tfvars files containing sensitive data in source control.
