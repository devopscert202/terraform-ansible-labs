# Lab 15 — Capstone projects

> **Goal:** Build a tagged VPC and public subnets using reusable input structures and workspace naming.
> **Time:** ~50 min · **Directory:** `terraform/extended/labs/lab15-capstone-projects/`

## Learning objectives

After completing this lab you will be able to:

- Assemble a root module with separate variables.tf
- Drive subnets with `for_each` on a typed map
- Apply workspace-based naming (`project-workspace`)
- Export vpc_id and public_subnet_ids for consumers
- Execute full plan/apply/destroy cycle in training account

## Architecture

Capstone root module: VPC + public subnets with workspace-aware naming and typed variables.

```hcl
# main.tf
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
}
provider "aws" { region = var.aws_region }

locals { name = "${var.project}-${terraform.workspace}" }
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  tags                 = merge(var.tags, { Name = local.name })
}
resource "aws_subnet" "public" {
  for_each                = var.public_subnets
  vpc_id                  = aws_vpc.this.id
  cidr_block              = each.value.cidr
  availability_zone       = each.value.az
  map_public_ip_on_launch = true
  tags                    = merge(var.tags, { Name = "${local.name}-${each.key}" })
}
output "vpc_id" { value = aws_vpc.this.id }
output "public_subnet_ids" { value = { for name, subnet in aws_subnet.public : name => subnet.id } }

# variables.tf
variable "aws_region" {
  type    = string
  default = "us-east-1"
}
variable "project" {
  type    = string
  default = "capstone"
}
variable "vpc_cidr" {
  type    = string
  default = "10.50.0.0/16"
}
variable "public_subnets" {
  type = map(object({ cidr = string, az = string }))
  default = {
    public_a = { cidr = "10.50.1.0/24", az = "us-east-1a" }
    public_b = { cidr = "10.50.2.0/24", az = "us-east-1b" }
  }
}
variable "tags" {
  type    = map(string)
  default = { managed_by = "terraform", course = "extended" }
}
```

**Example tfvars** (`terraform.tfvars.example`):

```hcl
aws_region = "us-east-1"
project    = "capstone"
# Do not place AWS credentials here. Use AWS_PROFILE or an IAM role.
```

```text
inputs ──► local.name = project-workspace
         ──► aws_vpc.this
         ──► aws_subnet.public[for_each]
         ──► outputs: vpc_id, public_subnet_ids
```

## Exercise index

| # | Exercise | Outcome |
|---|----------|----------|
| 1 | variables | Typed inputs |
| 2 | default apply | VPC + subnets |
| 3 | AWS verify | Console matches |
| 4 | dev workspace | Second stack |
| 5 | destroy all | Account clean |

## Prerequisites

- Terraform **1.5+** installed (`terraform version`)
- Terminal access to the lab directory
- For AWS labs: authenticated `AWS_PROFILE` or IAM role — **no access keys in `.tf` files**
- Read the matching doc in `terraform/extended/docs/` before applying cloud resources

## Before you start

```bash
cd terraform/extended/labs/lab15-capstone-projects
export AWS_PROFILE=your-training-profile   # when AWS is used
aws sts get-caller-identity                # verify account (AWS labs)
terraform version
```

**Validate**

```text
Terraform v1.5.x or newer is reported.
AWS identity matches your training account (if applicable).
```

### Step 1 — Survey project layout

Root module anatomy.

```bash
cd terraform/extended/labs/lab15-capstone-projects
ls *.tf
```

**Validate**

```text
main.tf, variables.tf present.
```

### Step 2 — Read variables

Typed objects for subnets and tags.

```bash
cat variables.tf
```

**Validate**

```text
public_subnets map, vpc_cidr, project, tags defaults.
```

### Step 3 — Copy tfvars example

Region/project without secrets.

```bash
cp terraform.tfvars.example terraform.tfvars
```

**Validate**

```text
tfvars ready for edits.
```

### Step 4 — Workspace naming

local.name uses workspace.

```bash
grep 'local.name' main.tf
terraform workspace show
```

**Validate**

```text
capstone-default expected.
```

### Step 5 — Format and init

AWS provider download.

```bash
terraform fmt
terraform init
terraform validate
```

**Validate**

```text
Valid capstone config.
```

### Step 6 — Plan in default

VPC + two subnets.

```bash
terraform plan
```

**Validate**

```text
3 resources to add; check CIDRs and AZs.
```

### Step 7 — Apply default workspace

Creates training VPC.

```bash
terraform apply
```

**Validate**

```text
vpc_id and public_subnet_ids outputs.
```

### Step 8 — Console verification

Match Terraform to AWS.

```bash
aws ec2 describe-vpcs --vpc-ids $(terraform output -raw vpc_id)
```

**Validate**

```text
VPC CIDR matches var.vpc_cidr.
```

### Step 9 — Verify subnets

for_each keys in output map.

```bash
terraform output public_subnet_ids
aws ec2 describe-subnets --filters Name=vpc-id,Values=$(terraform output -raw vpc_id)
```

**Validate**

```text
Two subnets in distinct AZs.
```

### Step 10 — Create dev workspace

Isolate capstone environments.

```bash
terraform workspace new dev
terraform apply
```

**Validate**

```text
Second VPC named capstone-dev (separate state).
```

### Step 11 — Tag inspection

merge(var.tags, ...) pattern.

```bash
aws ec2 describe-vpcs --vpc-ids $(terraform output -raw vpc_id) --query 'Vpcs[0].Tags'
```

**Validate**

```text
managed_by and course tags present.
```

### Step 12 — Modify subnet map

Practice object-typed variable.

```bash
# Edit terraform.tfvars public_subnets if desired
terraform plan
```

**Validate**

```text
Plan shows subnet updates only for changed attributes.
```

### Step 13 — Output contract

Document for Lab 11-style consumers.

```bash
terraform output -json > capstone-outputs.json
cat capstone-outputs.json
```

**Validate**

```text
JSON documents vpc_id and subnet map.
```

### Step 14 — Switch workspace cleanup

Destroy dev before default.

```bash
terraform workspace select dev
terraform destroy -auto-approve
```

**Validate**

```text
dev VPC removed.
```

### Step 15 — Destroy default

Leave account clean.

```bash
terraform workspace select default
terraform destroy -auto-approve
```

**Validate**

```text
No capstone VPCs remain.
```

## Design notes

Capstone modules are deployable units — pin versions, document inputs/outputs, and treat output renames as breaking changes. Workspace multiplies environments but not IAM boundaries; pair with separate state keys for production. This lab stops at public subnets; extending with IGW/routes is a natural follow-on exercise.

## Done when

- [ ] Deployed VPC with two public subnets
- [ ] Created dev workspace stack
- [ ] Destroyed all training resources
- [ ] Captured output JSON contract

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Provider initialization fails | Network, registry, or Terraform version | `terraform version`; rerun `terraform init` |
| Plan shows unexpected resources | Wrong workspace, tfvars, or state | `terraform workspace show`; inspect variables |
| AWS access denied | Profile/role lacks permission | `aws sts get-caller-identity` |
| Validation errors | Syntax or type mismatch | Read error path; run `terraform fmt` |
| Subnet CIDR conflict | Overlapping map values | Fix public_subnets |
| Invalid AZ | Region mismatch | Align az with aws_region |
| Recreate all subnets | Renamed map keys | Expected for_each behavior |

## Cleanup

```bash
terraform destroy -auto-approve
terraform workspace select default
terraform workspace delete dev 2>/dev/null || true
rm -f terraform.tfvars capstone-outputs.json
rm -rf .terraform terraform.tfstate* terraform.tfstate.d
```

Remove `.terraform/`, `terraform.tfstate*`, `backend.hcl`, and private `terraform.tfvars` before committing. Never commit secrets.

## Related resources

| Resource | Path |
|----------|------|
| Deep dive | [docs/projects/README.md](../docs/projects/README.md) |
| Interactive guide | `terraform/extended/html/` |
| Course README | `terraform/extended/README.md` |

---
*Deep dive: [docs/projects/README.md](../docs/projects/README.md) · Next: [Projects guide](../docs/projects/README.md) — curriculum complete*

## Reference — command cheat sheet


| Command | Purpose |
|---------|---------|
| `terraform fmt -recursive` | Canonical formatting |
| `terraform init` | Download providers and configure backend |
| `terraform validate` | Static type and reference checks |
| `terraform plan` | Propose infrastructure changes |
| `terraform apply` | Execute approved plan |
| `terraform destroy` | Tear down managed resources |
| `terraform state list` | List addresses in state |
| `terraform console` | Evaluate expressions interactively |

## Reference — ownership questions


Before every apply, answer:

1. Which AWS account and region will change?
2. Where is state stored and who else uses it?
3. What is the rollback plan if apply fails mid-way?
4. Who owns cleanup after the lab session ends?

Document answers in your lab notes — they mirror production change reviews.

## Reference — peer review prompts


Pair with a colleague and explain:

- What resources this root module owns
- Which variables are safe to change without replacement
- What outputs downstream stacks would consume
- How you would detect configuration drift

Peer review catches wrong-account applies before they happen.

## Reference — extending this lab


Optional extensions (not required for completion):

- Add variable validation blocks with `validation` stanzas
- Export additional outputs for a hypothetical consumer stack
- Wire an S3 remote backend using patterns from Labs 07–10
- Add `terraform.workspace` or `var.environment` to resource names

Keep extensions in a personal branch; do not commit training state.

## Reference — documentation links


| Topic | URL |
|-------|-----|
| Terraform language | https://developer.hashicorp.com/terraform/language |
| AWS provider | https://registry.terraform.io/providers/hashicorp/aws/latest/docs |
| CLI commands | https://developer.hashicorp.com/terraform/cli/commands |
| State storage | https://developer.hashicorp.com/terraform/language/state |

## Reference — delivery pipeline


```text
fmt → init → validate → plan (review) → apply → verify outputs → smoke test → document
```

In CI, run `terraform plan` on every pull request. Apply only from protected branches
with manual approval. Store plan artifacts (`plan.tfplan`) for audited applies.

## Reference — network extension


After completing Lab 15, add these resources in order:

1. `aws_internet_gateway` attached to VPC
2. `aws_route_table` with `0.0.0.0/0` → IGW
3. `aws_route_table_association` for each public subnet
4. Optional `aws_eip` + `aws_nat_gateway` for private subnets

Each addition should pass `terraform plan` with explicit review.

## Reference — multi-environment matrix


| Workspace | local.name | State file | AWS account |
|-----------|------------|------------|-------------|
| default | capstone-default | local or dev key | training |
| dev | capstone-dev | extended/dev/... | training |
| staging | capstone-staging | extended/staging/... | staging |

Align workspace strategy with organizational account boundaries.

## Reference — command cheat sheet (continued 2)


| Command | Purpose |
|---------|---------|
| `terraform fmt -recursive` | Canonical formatting |
| `terraform init` | Download providers and configure backend |
| `terraform validate` | Static type and reference checks |
| `terraform plan` | Propose infrastructure changes |
| `terraform apply` | Execute approved plan |
| `terraform destroy` | Tear down managed resources |
| `terraform state list` | List addresses in state |
| `terraform console` | Evaluate expressions interactively |

## Reference — ownership questions (continued 2)


Before every apply, answer:

1. Which AWS account and region will change?
2. Where is state stored and who else uses it?
3. What is the rollback plan if apply fails mid-way?
4. Who owns cleanup after the lab session ends?

Document answers in your lab notes — they mirror production change reviews.

## Reference — peer review prompts (continued 2)


Pair with a colleague and explain:

- What resources this root module owns
- Which variables are safe to change without replacement
- What outputs downstream stacks would consume
- How you would detect configuration drift

Peer review catches wrong-account applies before they happen.

## Reference — extending this lab (continued 2)


Optional extensions (not required for completion):

- Add variable validation blocks with `validation` stanzas
- Export additional outputs for a hypothetical consumer stack
- Wire an S3 remote backend using patterns from Labs 07–10
- Add `terraform.workspace` or `var.environment` to resource names

Keep extensions in a personal branch; do not commit training state.

## Reference — documentation links (continued 2)


| Topic | URL |
|-------|-----|
| Terraform language | https://developer.hashicorp.com/terraform/language |
| AWS provider | https://registry.terraform.io/providers/hashicorp/aws/latest/docs |
| CLI commands | https://developer.hashicorp.com/terraform/cli/commands |
| State storage | https://developer.hashicorp.com/terraform/language/state |

## Reference — delivery pipeline (continued 2)


```text
fmt → init → validate → plan (review) → apply → verify outputs → smoke test → document
```

In CI, run `terraform plan` on every pull request. Apply only from protected branches
with manual approval. Store plan artifacts (`plan.tfplan`) for audited applies.

## Reference — network extension (continued 2)


After completing Lab 15, add these resources in order:

1. `aws_internet_gateway` attached to VPC
2. `aws_route_table` with `0.0.0.0/0` → IGW
3. `aws_route_table_association` for each public subnet
4. Optional `aws_eip` + `aws_nat_gateway` for private subnets

Each addition should pass `terraform plan` with explicit review.

## Reference — multi-environment matrix (continued 2)


| Workspace | local.name | State file | AWS account |
|-----------|------------|------------|-------------|
| default | capstone-default | local or dev key | training |
| dev | capstone-dev | extended/dev/... | training |
| staging | capstone-staging | extended/staging/... | staging |

Align workspace strategy with organizational account boundaries.

## Reference — command cheat sheet (continued 3)


| Command | Purpose |
|---------|---------|
| `terraform fmt -recursive` | Canonical formatting |
| `terraform init` | Download providers and configure backend |
| `terraform validate` | Static type and reference checks |
| `terraform plan` | Propose infrastructure changes |
| `terraform apply` | Execute approved plan |
| `terraform destroy` | Tear down managed resources |
| `terraform state list` | List addresses in state |
| `terraform console` | Evaluate expressions interactively |

## Reference — ownership questions (continued 3)


Before every apply, answer:

1. Which AWS account and region will change?
2. Where is state stored and who else uses it?
3. What is the rollback plan if apply fails mid-way?
4. Who owns cleanup after the lab session ends?

Document answers in your lab notes — they mirror production change reviews.

## Reference — peer review prompts (continued 3)


Pair with a colleague and explain:

- What resources this root module owns
- Which variables are safe to change without replacement
- What outputs downstream stacks would consume
- How you would detect configuration drift

Peer review catches wrong-account applies before they happen.

## Reference — extending this lab (continued 3)


Optional extensions (not required for completion):

- Add variable validation blocks with `validation` stanzas
- Export additional outputs for a hypothetical consumer stack
- Wire an S3 remote backend using patterns from Labs 07–10
- Add `terraform.workspace` or `var.environment` to resource names

Keep extensions in a personal branch; do not commit training state.

## Reference — documentation links (continued 3)


| Topic | URL |
|-------|-----|
| Terraform language | https://developer.hashicorp.com/terraform/language |
| AWS provider | https://registry.terraform.io/providers/hashicorp/aws/latest/docs |
| CLI commands | https://developer.hashicorp.com/terraform/cli/commands |
| State storage | https://developer.hashicorp.com/terraform/language/state |

## Reference — delivery pipeline (continued 3)


```text
fmt → init → validate → plan (review) → apply → verify outputs → smoke test → document
```

In CI, run `terraform plan` on every pull request. Apply only from protected branches
with manual approval. Store plan artifacts (`plan.tfplan`) for audited applies.

## Reference — network extension (continued 3)


After completing Lab 15, add these resources in order:

1. `aws_internet_gateway` attached to VPC
2. `aws_route_table` with `0.0.0.0/0` → IGW
3. `aws_route_table_association` for each public subnet
4. Optional `aws_eip` + `aws_nat_gateway` for private subnets

Each addition should pass `terraform plan` with explicit review.

## Reference — multi-environment matrix (continued 3)


| Workspace | local.name | State file | AWS account |
|-----------|------------|------------|-------------|
| default | capstone-default | local or dev key | training |
| dev | capstone-dev | extended/dev/... | training |
| staging | capstone-staging | extended/staging/... | staging |

Align workspace strategy with organizational account boundaries.

## Reference — command cheat sheet (continued 4)


| Command | Purpose |
|---------|---------|
| `terraform fmt -recursive` | Canonical formatting |
| `terraform init` | Download providers and configure backend |
| `terraform validate` | Static type and reference checks |
| `terraform plan` | Propose infrastructure changes |
| `terraform apply` | Execute approved plan |
| `terraform destroy` | Tear down managed resources |
| `terraform state list` | List addresses in state |
| `terraform console` | Evaluate expressions interactively |

## Reference — ownership questions (continued 4)


Before every apply, answer:

1. Which AWS account and region will change?
2. Where is state stored and who else uses it?
3. What is the rollback plan if apply fails mid-way?
4. Who owns cleanup after the lab session ends?

Document answers in your lab notes — they mirror production change reviews.

## Reference — peer review prompts (continued 4)


Pair with a colleague and explain:

- What resources this root module owns
- Which variables are safe to change without replacement
- What outputs downstream stacks would consume
- How you would detect configuration drift

Peer review catches wrong-account applies before they happen.
