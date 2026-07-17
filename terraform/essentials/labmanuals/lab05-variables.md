# Lab 05 — Variables and Locals

**Course alignment:** L10 AP-02  
**Objective:** Use typed input variables, a local tag map, a data source, and an output for an EC2 instance.

## Prerequisites

- Terraform 1.5+ installed (`terraform version`).
- For AWS labs, authenticate through `AWS_PROFILE` or an IAM role; credentials must not be placed in `.tf` files.
- Work from `../labs/lab05-variables`.

## Procedure

### 1. Set `AWS_PROFILE` or use an IAM role, then verify access with `aws sts get-caller-identity`.

Set `AWS_PROFILE` or use an IAM role, then verify access with `aws sts get-caller-identity`.

**Validate:** Check the stated result before continuing.

### 2. In `labs/lab05-variables`, run `terraform init && terraform validate`

In `labs/lab05-variables`, run `terraform init && terraform validate`; verify both commands succeed.

**Validate:** Check the stated result before continuing.

### 3. Run `terraform plan -var="server_name=my-lab-web"`

Run `terraform plan -var="server_name=my-lab-web"`; verify the instance tags include the supplied Name and `ManagedBy = Terraform`.

**Validate:** Check the stated result before continuing.

### 4. Apply only after reviewing the plan: `terraform apply -var="server_name=my-lab-web"`.

Apply only after reviewing the plan: `terraform apply -var="server_name=my-lab-web"`.

**Validate:** Confirm the command exits with status 0 and the expected result is visible.

### 5. Run `terraform output instance_arn`

Run `terraform output instance_arn`; verify an ARN is returned.

**Validate:** Check the stated result before continuing.

### 6. Run `terraform destroy -var="server_name=my-lab-web"`

Run `terraform destroy -var="server_name=my-lab-web"`; verify the instance is removed.

**Validate:** Check the stated result before continuing.

## Cleanup and evidence

For AWS labs, destruction is mandatory after verification. Record the Terraform version, the reviewed plan summary, and the final destroy result. Do not retain state files or tfvars files containing sensitive data in source control.
