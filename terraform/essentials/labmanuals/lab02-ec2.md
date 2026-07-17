# Lab 02 — Deploy an EC2 Instance

**Course alignment:** L7 AP-02  
**Objective:** Use a data source to select a current Ubuntu AMI and provision a tagged EC2 instance without embedded credentials.

## Prerequisites

- Terraform 1.5+ installed (`terraform version`).
- For AWS labs, authenticate through `AWS_PROFILE` or an IAM role; credentials must not be placed in `.tf` files.
- Work from `../labs/lab02-ec2`.

## Procedure

### 1. Set a profile or use an IAM role. For a profile: `export AWS_PROFILE=your-profile`.

Set a profile or use an IAM role. For a profile: `export AWS_PROFILE=your-profile`.

**Validate:** Confirm the command exits with status 0 and the expected result is visible.

### 2. Verify identity: `aws sts get-caller-identity`

Verify identity: `aws sts get-caller-identity`; confirm the expected account and role/user.

**Validate:** Check the stated result before continuing.

### 3. In `labs/lab02-ec2`, run `terraform init && terraform validate`

In `labs/lab02-ec2`, run `terraform init && terraform validate`; verify validation succeeds.

**Validate:** Check the stated result before continuing.

### 4. Run `terraform plan`

Run `terraform plan`; verify one `aws_instance.web` is proposed and review the selected region and instance type.

**Validate:** Check the stated result before continuing.

### 5. Run `terraform apply`

Run `terraform apply`; type `yes` only after reviewing the plan. Verify `instance_id` and `public_ip` outputs.

**Validate:** Check the stated result before continuing.

### 6. Run `terraform destroy`

Run `terraform destroy`; type `yes` and verify the EC2 instance is removed.

**Validate:** Check the stated result before continuing.

## Cleanup and evidence

For AWS labs, destruction is mandatory after verification. Record the Terraform version, the reviewed plan summary, and the final destroy result. Do not retain state files or tfvars files containing sensitive data in source control.
