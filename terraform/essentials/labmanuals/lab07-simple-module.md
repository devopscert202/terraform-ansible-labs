# Lab 07 — Simple Module

> **Goal:** Call a reusable local **network module** that creates a VPC and subnet, passing inputs and reading module outputs from the root module.
> **Time:** ~60 min · **Difficulty:** Intermediate · **Files:** `labs/lab07-simple-module/`

## Overview

Real Terraform codebases split infrastructure into **modules** — reusable packages with their own variables, resources, and outputs. This lab deploys a minimal networking stack: a VPC and one subnet inside a child module at `modules/network/`.

The root module (`main.tf`) configures the AWS provider and calls `module "network"`, passing CIDR blocks and a name prefix. Module outputs (`vpc_id`, `subnet_id`) surface back to the root for verification. No credentials appear inside the module — provider configuration is inherited from the parent.

## Learning objectives

- Inspect a local module's `variables.tf`, `main.tf`, and `outputs.tf`
- Call a module with the `module` block and `source = "./modules/network"`
- Run `terraform init` to install child module dependencies
- Read a plan showing module resources (`module.network.aws_vpc.this`, etc.)
- Apply, verify outputs, and destroy VPC resources

## Prerequisites

- [ ] Terraform 1.5+ installed (`terraform version`)
- [ ] AWS CLI configured OR IAM role on lab instance
- [ ] IAM permissions for VPC create/describe/delete
- [ ] Labs 02 and 05 complete (EC2 and variables)
- [ ] Working directory: `terraform/essentials/labs/lab07-simple-module`

## What you will build

```
terraform/essentials/labs/lab07-simple-module/
├── main.tf                      # provider, module call, root outputs
├── variables.tf                 # aws_region, name, vpc_cidr, subnet_cidr
├── modules/
│   └── network/
│       ├── main.tf              # aws_vpc, aws_subnet
│       ├── variables.tf         # name, vpc_cidr, subnet_cidr
│       └── outputs.tf           # vpc_id, subnet_id
└── terraform.tfstate
```

```
  root main.tf
       │
       │  module "network" { source = "./modules/network" }
       ▼
  modules/network/main.tf
       │
       ├── aws_vpc.this      (10.42.0.0/16)
       └── aws_subnet.this   (10.42.1.0/24)
       │
       ▼
  root outputs: vpc_id, subnet_id
```

---

## Exercise 1 — Authenticate and explore module layout

<a id="ex1"></a>

### Step 1.1 — Navigate to the lab directory

```bash
cd ~/terraform-ansible-labs/terraform/essentials/labs/lab07-simple-module
```

**Validate**

```bash
ls -la
```

Directory contains `main.tf`, `variables.tf`, and `modules/network/`.

**What happened:** The root module orchestrates; the child module encapsulates networking resources.

### Step 1.2 — Set AWS profile (skip if using IAM role)

```bash
export AWS_PROFILE=training
```

**Validate**

```bash
aws sts get-caller-identity --query Arn --output text
```

```text
arn:aws:iam::123456789012:user/training-user
```

**What happened:** Provider credentials are configured only in the root module. Child modules inherit the parent's provider configuration.

### Step 1.3 — List module directory contents

```bash
ls -la modules/network/
```

**Validate** — contains `main.tf`, `variables.tf`, and `outputs.tf`. No `provider` block with embedded keys.

**What happened:** Modules should not hardcode credentials. The root module's `provider "aws"` applies to resources in child modules.

---

## Exercise 2 — Read module and root configuration

<a id="ex2"></a>

### Step 2.1 — Display module files

```bash
cat modules/network/variables.tf modules/network/main.tf modules/network/outputs.tf
```

**Validate** — module requires `name`, `vpc_cidr`, `subnet_cidr`; creates `aws_vpc.this` and `aws_subnet.this`; outputs `vpc_id` and `subnet_id`.

**What happened:** Child modules declare inputs, resources, and outputs. Terraform addresses resources as `module.network.aws_vpc.this` in plans and state.

### Step 2.2 — Display root module call

```bash
cat main.tf variables.tf
```

**Validate** — root `module "network"` block passes `var.name`, `var.vpc_cidr`, `var.subnet_cidr` with defaults `10.42.0.0/16` and `10.42.1.0/24`.

**What happened:** The root module wires variables into the child module. Provider configuration stays in the root — not in the module.

### Step 2.3 — Confirm no credentials in module tree

```bash
grep -rE 'access_key|secret_key' modules/ || echo "No embedded credentials — good"
```

**Validate**

```text
No embedded credentials — good
```

**What happened:** Modules distributed via git or a registry must never contain secrets.

---

## Exercise 3 — Initialize and validate

<a id="ex3"></a>

### Step 3.1 — Run terraform init

```bash
terraform init
```

**Validate**

```text
Terraform has been successfully initialized!
```

Output mentions installing modules from `modules/network`.

**What happened:** `init` downloads providers **and** installs local/remote modules into `.terraform/modules/`.

### Step 3.2 — Validate entire configuration including modules

```bash
terraform validate
```

**Validate**

```text
Success! The configuration is valid.
```

**What happened:** Validation traverses the module tree and checks provider schemas for all resources.

---

## Exercise 4 — Plan module resources

<a id="ex4"></a>

### Step 4.1 — Run terraform plan

```bash
terraform plan
```

**Validate** — plan summary includes:

```text
Plan: 2 to add, 0 to change, 0 to destroy.
```

**What happened:** Two resources — VPC and subnet — will be created inside the child module.

### Step 4.2 — Confirm module resource addresses and CIDRs

Scroll through plan output.

**Validate** — shows `+ module.network.aws_vpc.this` with `cidr_block = "10.42.0.0/16"` and `+ module.network.aws_subnet.this` with `cidr_block = "10.42.1.0/24"`.

**What happened:** Module resources are prefixed with `module.<MODULE_NAME>.` in plans and state.

---

## Exercise 5 — Apply and verify outputs

<a id="ex5"></a>

### Step 5.1 — Apply the configuration

```bash
terraform apply
```

Review the plan when prompted. Type `yes` to confirm.

**Validate**

```text
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.
```

**What happened:** AWS created the VPC and subnet. State records them under module addresses.

### Step 5.2 — Read module outputs

```bash
terraform output
```

**Validate**

```text
subnet_id = "subnet-0abc123def456789"
vpc_id    = "vpc-0abc123def456789"
```

Both IDs are non-empty.

**What happened:** Root outputs forward values from `module.network` outputs.

### Step 5.3 — Verify VPC CIDR in AWS

```bash
aws ec2 describe-vpcs --vpc-ids $(terraform output -raw vpc_id) --query 'Vpcs[0].CidrBlock' --output text
```

**Validate**

```text
10.42.0.0/16
```

**What happened:** Cross-checking AWS confirms Terraform state matches reality.

---

## Exercise 6 — Destroy module resources

<a id="ex6"></a>

### Step 6.1 — Destroy all resources

```bash
terraform destroy
```

Type `yes` when prompted.

**Validate**

```text
Destroy complete! Resources: 2 destroyed.
```

**What happened:** AWS removed subnet then VPC. Module destruction is identical to root resource destruction from the operator's perspective.

### Step 6.2 — Confirm empty state

```bash
terraform state list
```

**Validate** — no output.

**What happened:** Always destroy VPC lab resources — idle VPCs are usually free but violate lab hygiene and clutter the console.

---

## Key takeaways

- **Modules** bundle reusable infrastructure with their own variables, resources, and outputs
- Root modules call child modules via `module` blocks; `source` can be local or remote
- Plan/state addresses use `module.<name>.<resource>` prefixing
- Child modules inherit provider configuration from the parent — no duplicate provider blocks needed
- `terraform init` installs modules; re-run after adding or changing module sources

## Done when

- [ ] `aws sts get-caller-identity` succeeded
- [ ] Module directory inspected — no embedded credentials
- [ ] `terraform init` discovered local `network` module
- [ ] `terraform plan` showed 2 resources under `module.network`
- [ ] `terraform apply` completed with `vpc_id` and `subnet_id` outputs
- [ ] AWS CLI confirmed VPC CIDR `10.42.0.0/16`
- [ ] `terraform destroy` removed both resources

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `Module not installed` | Skipped init | Run `terraform init` |
| `no matching VPC found` on destroy | Already deleted manually | `terraform refresh` or remove from state |
| `Error creating VPC: VpcLimitExceeded` | Account VPC quota | Delete unused VPCs or request quota increase |
| `InvalidSubnet.Range` | Subnet CIDR outside VPC | Ensure `subnet_cidr` is inside `vpc_cidr` |
| `UnauthorizedOperation` | Missing EC2/VPC IAM permissions | Request lab VPC policy |
| Module changes not detected | Cached modules | Run `terraform init -upgrade` |

## Cleanup

```bash
cd ~/terraform-ansible-labs/terraform/essentials/labs/lab07-simple-module
terraform destroy -auto-approve 2>/dev/null || true
rm -f terraform.tfstate.backup
```

Verify zero VPCs tagged `terraform-essentials-vpc` in the AWS VPC console.

## Next steps

- [Lab 08 — tfvars, validation, and secrets](lab08-tfvars-secrets.md)
- [Modules (interactive HTML)](../html/modules.html)
- [Modules doc](../docs/05-modules/README.md)

---
*Source: Terraform Essentials bootcamp · L8 Lesson-End Project · Next: [lab08](lab08-tfvars-secrets.md)*
