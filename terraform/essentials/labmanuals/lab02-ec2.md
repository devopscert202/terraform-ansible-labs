# Lab 02 — Deploy an EC2 Instance

| | |
|---|---|
| **Goal** | Use an AMI data source to select Ubuntu 22.04 and provision a tagged EC2 instance without embedding credentials. |
| **Time** | 35–45 minutes |
| **Difficulty** | Beginner |
| **Files** | `labs/lab02-ec2/main.tf`, `variables.tf`, `terraform.tfvars.example` |

## Overview

This lab applies the provider and resource concepts from Labs 01 and the docs to a real AWS EC2 instance. You will use a **data source** to resolve the latest Canonical Ubuntu AMI dynamically instead of hard-coding an AMI ID that expires. The **resource** `aws_instance.web` is what Terraform creates and tracks in state.

Authentication uses the standard AWS credential chain. You will set `AWS_PROFILE` in your shell — credentials never appear in `.tf` files. This lab incurs a small EC2 cost until you destroy resources.

## Learning objectives

After completing this lab you will be able to:

- Configure the AWS provider with `region = var.aws_region`
- Use `data.aws_ami` with filters to select an AMI
- Deploy `aws_instance.web` with tags
- Read `instance_id` and `public_ip` outputs
- Run the full init → plan → apply → destroy workflow on AWS

## Prerequisites checklist

- [ ] Terraform 1.5+ installed
- [ ] AWS CLI installed
- [ ] AWS account with EC2 permissions (`RunInstances`, `DescribeInstances`, `DescribeImages`)
- [ ] Named AWS profile configured in `~/.aws/credentials`
- [ ] Lab 01 completed (understanding of init/validate)

## What you will build

| Resource | Type | Purpose |
|----------|------|---------|
| `data.aws_ami.ubuntu` | Data source | Latest Ubuntu 22.04 HVM AMI |
| `aws_instance.web` | Resource | `t3.micro` instance with tags |
| Outputs | `instance_id`, `public_ip` | Verification values |

Default tags include `Name = terraform-essentials-web`, `ManagedBy = Terraform`, `Lab = terraform-essentials-lab02`.

## Exercise index

| Exercise | Topic | Steps |
|----------|-------|-------|
| 1 | AWS authentication | 1.1 – 1.2 |
| 2 | Initialize and validate | 2.1 – 2.3 |
| 3 | Plan review | 3.1 – 3.2 |
| 4 | Apply and verify | 4.1 – 4.3 |
| 5 | Destroy and cleanup | 5.1 – 5.2 |

---

## Exercise 1 — AWS authentication

### Step 1.1 — Set AWS profile

Export your profile name. Replace `training` with your actual profile.

```bash
export AWS_PROFILE=training
```

**Validate:**

```bash
echo $AWS_PROFILE
```

Expected: `training` (or your profile name).

**What happened:** The AWS provider and AWS CLI both read credentials from this profile. No keys are stored in Terraform source.

### Step 1.2 — Verify caller identity

Confirm the profile resolves to the expected account before creating resources.

```bash
aws sts get-caller-identity
```

**Validate:** JSON output with non-empty `Account`, `Arn`, and `UserId` fields.

**What happened:** This proves your credential chain works independently of Terraform.

---

## Exercise 2 — Initialize and validate

### Step 2.1 — Change to lab directory

```bash
cd terraform/essentials/labs/lab02-ec2
```

**Validate:** `ls main.tf variables.tf` shows both files.

**What happened:** This directory is the root module for Lab 02.

### Step 2.2 — Initialize Terraform

```bash
terraform init
```

**Validate:** Output ends with `Terraform has been successfully initialized!`

**What happened:** Terraform downloaded `hashicorp/aws` ~> 5.0 and wrote `.terraform.lock.hcl`.

### Step 2.3 — Validate configuration

```bash
terraform validate
```

**Validate:**

```
Success! The configuration is valid.
```

**What happened:** Configuration syntax and references are correct. Validate does not check AWS permissions.

---

## Exercise 3 — Plan review

### Step 3.1 — Run terraform plan

Preview changes without modifying infrastructure.

```bash
terraform plan
```

**Validate:** Plan summary includes:

```
Plan: 1 to add, 0 to change, 0 to destroy.
```

And a line creating `aws_instance.web`.

**What happened:** Terraform will create one EC2 instance. The AMI comes from `data.aws_ami.ubuntu.id` (read during plan/apply).

### Step 3.2 — Confirm instance settings in plan

Scroll the plan output and verify:

- `instance_type` = `t3.micro` (default)
- `region` effective value is `us-east-1` (default `var.aws_region`)
- Tags include `ManagedBy = "Terraform"`

**Validate:** Values match `variables.tf` defaults unless you passed overrides.

**What happened:** The plan is your safety review — always read it before apply.

---

## Exercise 4 — Apply and verify

### Step 4.1 — Apply configuration

```bash
terraform apply
```

Review the plan shown again. Type `yes` when prompted.

**Validate:** Output includes:

```
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
```

**What happened:** The AWS provider called EC2 CreateInstance. State now stores the instance ID.

### Step 4.2 — Read outputs

```bash
terraform output instance_id
```

**Validate:** Value starts with `i-` (e.g., `"i-0abc123def456"`).

```bash
terraform output public_ip
```

**Validate:** An IP address string or empty if no public IP was assigned (default VPC behavior varies).

**What happened:** Outputs expose resource attributes defined in `main.tf`.

### Step 4.3 — Optional AWS CLI verification

```bash
aws ec2 describe-instances --instance-ids $(terraform output -raw instance_id) --query 'Reservations[0].Instances[0].State.Name' --output text
```

**Validate:** `running` or `pending`.

**What happened:** Cross-checks Terraform state against the live AWS API.

---

## Exercise 5 — Destroy and cleanup

### Step 5.1 — Destroy infrastructure

**Mandatory** — do not leave EC2 running after the lab.

```bash
terraform destroy
```

Type `yes` when prompted.

**Validate:**

```
Destroy complete! Resources: 0 added, 0 changed, 1 destroyed.
```

**What happened:** EC2 instance terminated; removed from state.

### Step 5.2 — Confirm empty state

```bash
terraform state list
```

**Validate:** No resources listed (or command reports state is empty).

**What happened:** No managed resources remain.

---

## Optional — Override variables

Copy the example file only as a reference. Actual variables in `variables.tf` are `aws_region`, `instance_type`, and `instance_name`:

```bash
terraform plan -var="instance_name=my-lab-server"
```

Or create `terraform.tfvars` (add to `.gitignore` if needed):

```hcl
aws_region    = "us-east-1"
instance_type = "t3.micro"
instance_name = "terraform-essentials-web"
```

---

## Done when

- [ ] `aws sts get-caller-identity` succeeded with `AWS_PROFILE`
- [ ] `terraform init` and `validate` succeeded
- [ ] Plan showed exactly **1 to add** for `aws_instance.web`
- [ ] Apply produced `instance_id` output
- [ ] `terraform destroy` completed successfully
- [ ] No EC2 instances remain from this lab

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `No valid credential sources` | Profile not set | `export AWS_PROFILE=...` |
| `UnauthorizedOperation` | IAM lacks EC2 permissions | Add EC2 policy to IAM user/role |
| `InvalidAMIID.NotFound` | AMI filter mismatch | Verify region is `us-east-1`; check data source |
| `InstanceLimitExceeded` | Account vCPU limit | Request limit increase or use different region |
| Plan shows 0 to add | Wrong directory or already applied | Check `pwd`; run `terraform state list` |
| `Error acquiring state lock` | Stale lock (rare in local state) | Ensure no other terraform process running |
| Destroy fails | Dependency or permission | Check AWS console; retry destroy |

## Cleanup

```bash
export AWS_PROFILE=training
cd terraform/essentials/labs/lab02-ec2
terraform destroy
```

If destroy fails, find the instance in the EC2 console (tag `Lab = terraform-essentials-lab02`) and terminate manually, then:

```bash
terraform state rm aws_instance.web
```

## Key takeaways

1. **Data sources** resolve AMIs; **resources** create instances.
2. Use **`AWS_PROFILE`** — never `access_key` in HCL.
3. Always **review plan** before typing `yes`.
4. **Destroy** AWS resources immediately after verification.
5. **Outputs** provide instance ID for CLI cross-checks.

## Next steps

- Read [docs/03-resources/README.md](../docs/03-resources/README.md)
- Open [html/foundations.html](../html/foundations.html)
- Continue to [Lab 03 — Plan/Apply/Destroy](lab03-plan-apply-destroy.md)
