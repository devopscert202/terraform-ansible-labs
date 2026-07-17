# Lab 01 — Providers and Initialization

**Course alignment:** L8 AP-01  
**Objective:** Configure version constraints for AWS and Random providers, initialize the working directory, and inspect installed provider requirements.

## Prerequisites

- Terraform 1.5+ installed (`terraform version`).
- For AWS labs, authenticate through `AWS_PROFILE` or an IAM role; credentials must not be placed in `.tf` files.
- Work from `../labs/lab01-providers-init`.

## Procedure

### 1. Confirm the Terraform CLI is 1.5 or later: `terraform version`.

Confirm the Terraform CLI is 1.5 or later: `terraform version`.

**Validate:** Confirm the command exits with status 0 and the expected result is visible.

### 2. Open `labs/lab01-providers-init` and inspect `main.tf`

Open `labs/lab01-providers-init` and inspect `main.tf`; verify AWS is constrained to `~> 5.0` and no credentials appear in code.

**Validate:** Check the stated result before continuing.

### 3. Run `terraform init`

Run `terraform init`; verify the command completes and creates `.terraform.lock.hcl`.

**Validate:** Check the stated result before continuing.

### 4. Run `terraform providers`

Run `terraform providers`; verify both `hashicorp/aws` and `hashicorp/random` are listed.

**Validate:** Check the stated result before continuing.

### 5. Run `terraform validate`

Run `terraform validate`; verify `Success! The configuration is valid.`

**Validate:** Check the stated result before continuing.

## Cleanup and evidence

For AWS labs, destruction is mandatory after verification. Record the Terraform version, the reviewed plan summary, and the final destroy result. Do not retain state files or tfvars files containing sensitive data in source control.
