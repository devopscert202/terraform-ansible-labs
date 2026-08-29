# Lab 06 — Variables and Outputs

| | |
|---|---|
| **Goal** | Replace the hardcoded values in an EC2 configuration with variables, compute a tag map with `locals`, and read results back with outputs. |
| **Time** | 40–50 minutes |
| **Tier** | Intermediate |
| **Files** | `terraform/labs/lab06-variables-outputs/` |

## Overview

So far every value you wrote was fixed in the file. Change the region and you edit the file. A
**variable** is a named input you declare once and pass a value to from outside, so one configuration
can serve dev, test, and prod. An **output** is a named value Terraform prints after `apply` so you
can read an ID or IP address without hunting through the AWS console. A **local** is a value the
configuration works out for itself; nobody outside can set it.

This lab rebuilds the single EC2 instance from Lab 03, but the region, name, size, and tags now
arrive as variables, and the tag set is assembled by a local. Those three ideas — inputs, computed
internals, and published results — are the foundation for every lab that follows.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `data.aws_ami.al2023` | Looks up the newest Amazon Linux 2023 image | Free |
| `aws_instance.web` | One `t3.micro` instance, tagged from a local | Free tier, otherwise a few cents/hour |
| 4 variables | `aws_region`, `server_name`, `instance_type`, `tags` | — |
| 1 local | `common_tags`, built with `merge()` | — |
| 4 outputs | `instance_id`, `instance_arn`, `public_ip`, `applied_tags` | — |

## Before you start

- [ ] Lab 05 completed ([lab05-fmt-validate.md](lab05-fmt-validate.md))
- [ ] AWS credentials exported and `aws sts get-caller-identity` succeeds
- [ ] Working directory: `../labs/lab06-variables-outputs/`
- [ ] A default VPC exists in `us-east-1` — this instance has no `subnet_id`, so it needs one, exactly as in [Lab 03](lab03-first-ec2.md):

```bash
aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[].VpcId' --output text
```

If that prints nothing, run `aws ec2 create-default-vpc` once. `terraform plan` will not warn
you; the apply is where it fails.

## Steps

### Step 1 — Read the variable declarations

```bash
cd terraform/labs/lab06-variables-outputs
cat variables.tf
```

**Expected output**

```text
variable "aws_region" {
  type        = string
  description = "AWS region the instance is created in."
  default     = "us-east-1"
}

variable "server_name" {
  type        = string
  description = "Value used for the Name tag on the EC2 instance."
  default     = "lab06-web"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance size."
  default     = "t3.micro"
}

variable "tags" {
  type        = map(string)
  description = "Extra tags merged into every resource tag set."
  default = {
    Environment = "training"
    Owner       = "platform-team"
  }
}
```

Each `variable` block has three parts you must always write: a name, a `type`, and a `description`.
`default` is optional — a variable without one is required, and Terraform will refuse to run until
you supply a value. `type = string` accepts text; `type = map(string)` accepts a set of key/value
pairs, which is how `tags` carries several tags in one value.

### Step 2 — Read the locals block

```bash
grep -A 6 'locals {' main.tf
```

**Expected output**

```text
locals {
  common_tags = merge(var.tags, {
    Name = var.server_name
    Lab  = "lab06"
  })
}
```

`merge()` combines two maps into one. You reference a variable as `var.NAME` and a local as
`local.NAME`. The instance sets `tags = local.common_tags`, so the tagging rule is written once no
matter how many resources later use it.

### Step 3 — Read the outputs

```bash
cat outputs.tf
```

**Expected output**

```text
output "instance_id" {
  description = "EC2 instance ID."
  value       = aws_instance.web.id
}

output "instance_arn" {
  description = "Full Amazon Resource Name of the instance."
  value       = aws_instance.web.arn
}

output "public_ip" {
  description = "Public IPv4 address assigned to the instance."
  value       = aws_instance.web.public_ip
}

output "applied_tags" {
  description = "The merged tag map that was applied to the instance."
  value       = local.common_tags
}
```

An output's `value` can be a resource attribute or, as in `applied_tags`, a local. Outputs are how a
configuration publishes results — to you on screen now, and to other configurations in Lab 20.

### Step 4 — Initialize

```bash
terraform init
```

**Expected output**

```text
Terraform has been successfully initialized!
```

### Step 5 — Validate

```bash
terraform validate
```

**Expected output**

```text
Success! The configuration is valid.
```

This checks types and references without contacting AWS, so a misspelled `var.` name is caught here
rather than halfway through an apply.

### Step 6 — Watch `merge()` build the tag map

```bash
echo 'var.tags' | terraform console
echo 'local.common_tags' | terraform console
```

**Expected output**

```text
tomap({
  "Environment" = "training"
  "Owner" = "platform-team"
})
{
  "Environment" = "training"
  "Lab" = "lab06"
  "Name" = "lab06-web"
  "Owner" = "platform-team"
}
```

Two tags went in and four came out. This works before anything exists in AWS, because locals and
variables are computed entirely inside Terraform. It is the cheapest way to check tagging logic.

### Step 7 — Plan with the defaults

```bash
terraform plan
```

**Expected output**

```text
Plan: 1 to add, 0 to change, 0 to destroy.
```

Every variable has a default, so the plan works with no input from you. The instance's tag block in
the plan shows the same four tags you saw in Step 6.

### Step 8 — Override one value on the command line

```bash
terraform plan -var 'server_name=lab06-cli-web'
```

The `Name` tag in the plan is now `lab06-cli-web`, while `Environment` and `Owner` are untouched —
`merge()` replaced one key and left the rest. `-var` beats the default. Lab 07 covers the other ways
to supply values and the order Terraform applies them in.

### Step 9 — Apply

```bash
terraform apply
```

Type `yes` at the prompt.

**Expected output**

```text
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

applied_tags = {
  "Environment" = "training"
  "Lab" = "lab06"
  "Name" = "lab06-web"
  "Owner" = "platform-team"
}
instance_arn = "arn:aws:ec2:us-east-1:111122223333:instance/i-0abc123def4567890"
instance_id = "i-0abc123def4567890"
public_ip = "203.0.113.25"
```

Your account number, instance ID, and IP will differ.

### Step 10 — List the outputs again without applying

```bash
terraform output
```

Outputs are stored in state, so you can re-read them at any time without running `apply` again. This
is the everyday way to get an ID back after closing your terminal.

### Step 11 — Read a single output for scripting

```bash
terraform output -raw instance_id
```

**Expected output**

```text
i-0abc123def4567890
```

`-raw` prints the bare value with no quotes, which is what you want when feeding it into another
command.

### Step 12 — Confirm the tags reached AWS

```bash
aws ec2 describe-tags \
  --filters "Name=resource-id,Values=$(terraform output -raw instance_id)" \
  --query 'Tags[].[Key,Value]' --output text
```

**Expected output**

```text
Environment	training
Lab	lab06
Name	lab06-web
Owner	platform-team
```

The command substitution is why Step 11 mattered. All four tags from `local.common_tags` are on the
real instance, which closes the loop from variable to local to resource to AWS.

### Step 13 — Destroy

```bash
terraform destroy
```

Type `yes` at the prompt.

**Expected output**

```text
Destroy complete! Resources: 1 destroyed.
```

## Done when

- [ ] `terraform validate` succeeds
- [ ] `terraform console` shows `var.tags` with two entries and `local.common_tags` with four
- [ ] `terraform plan` succeeds using defaults alone
- [ ] `-var 'server_name=...'` visibly changes only the `Name` tag in the plan
- [ ] `apply` prints all four outputs
- [ ] `terraform output -raw instance_id` prints a bare instance ID
- [ ] `describe-tags` returns four tags, including `Lab = lab06`
- [ ] `terraform destroy` reports `1 destroyed`

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `No value for required variable` | Variable has no `default` and none was supplied | Add `default`, or pass `-var 'name=value'` |
| `Invalid value for module argument` | Wrong type, e.g. a string where a map is expected | Match the `type` in `variables.tf` |
| `Reference to undeclared local value` | Used `local.x` before adding it to the `locals` block | Declare it in `locals` |
| `No valid credential sources found` | Credentials not exported in this shell | Re-export the keys from Lab 00 |
| Tags missing on the instance | `tags` argument not wired to the local | Confirm `tags = local.common_tags` |
| `Output "instance_id" not found` | `apply` has not run, or you are in another directory | `pwd`, then `terraform apply` |
| `InvalidAMIID.NotFound` | AMI lookup returned nothing in this region | Confirm `aws_region` is `us-east-1` |
| `VPCIdNotSpecified: No default VPC for this user` on apply, after a clean plan | The account has no default VPC for the instance to launch into ([Lab 03](lab03-first-ec2.md)) | `aws ec2 create-default-vpc`, then `terraform apply` again |

## Cleanup

```bash
terraform destroy
```

## Next steps

- Deep dive: [docs/intermediate/06-variables.md](../docs/intermediate/06-variables.md)
- Visual: [html/intermediate.html](../html/intermediate.html)
- Continue to [Lab 07 — tfvars and Secrets](lab07-tfvars-secrets.md)
