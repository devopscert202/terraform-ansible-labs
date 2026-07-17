# Lab 07 — Simple Module

**Course alignment:** L8 Lesson-End Project (condensed)  
**Objective:** Call a reusable local network module that creates a VPC and a subnet.

## Prerequisites

- Terraform 1.5+ installed (`terraform version`).
- For AWS labs, authenticate through `AWS_PROFILE` or an IAM role; credentials must not be placed in `.tf` files.
- Work from `../labs/lab07-simple-module`.

## Procedure

### 1. Set `AWS_PROFILE` or use an IAM role, then verify access with `aws sts get-caller-identity`.

Set `AWS_PROFILE` or use an IAM role, then verify access with `aws sts get-caller-identity`.

**Validate:** Check the stated result before continuing.

### 2. From `labs/lab07-simple-module`, inspect `modules/network`

From `labs/lab07-simple-module`, inspect `modules/network`; verify it contains inputs and outputs but no provider credentials.

**Validate:** Check the stated result before continuing.

### 3. Run `terraform init && terraform validate`

Run `terraform init && terraform validate`; verify Terraform discovers the local module and validation succeeds.

**Validate:** Check the stated result before continuing.

### 4. Run `terraform plan`

Run `terraform plan`; verify the module proposes one VPC and one subnet with the configured CIDRs.

**Validate:** Check the stated result before continuing.

### 5. Run `terraform apply`

Run `terraform apply`; type `yes`, then verify `terraform output vpc_id` and `terraform output subnet_id` return IDs.

**Validate:** Check the stated result before continuing.

### 6. Run `terraform destroy`

Run `terraform destroy`; type `yes` and verify both resources are removed.

**Validate:** Check the stated result before continuing.

## Cleanup and evidence

For AWS labs, destruction is mandatory after verification. Record the Terraform version, the reviewed plan summary, and the final destroy result. Do not retain state files or tfvars files containing sensitive data in source control.
