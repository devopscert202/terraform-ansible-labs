# Getting Started with Terraform

## Objective (conceptual)

Terraform is a declarative infrastructure-as-code (IaC) tool: you describe the **desired end state** in HashiCorp Configuration Language (HCL), and Terraform reconciles real infrastructure to match that description. The mental model is not a shell script of API calls—it is a **specification** that Terraform reads, compares against **state** (what it already manages), and changes only when the plan shows a diff.

For beginners, Terraform is often the first tool that makes environments reproducible. The same `.tf` files that build a training lab can build staging or production when you change input values—not when you rewrite console clicks. Each lab in `terraform/essentials/labs/` is an isolated **root module** with its own state so experiments do not collide.

**Interactive reference:** [Foundations](../../html/foundations.html)

## Configuration, providers, and resources

- **Configuration** — `.tf` files in a working directory (one lab folder = one root module).
- **Provider** — Plugin that speaks to an API (`hashicorp/aws`, `hashicorp/random`).
- **Resource** — Object Terraform creates, updates, and destroys (`aws_instance`, `random_pet`).
- **Data source** — Read-only lookup of existing values (covered in Lab 02).
- **Output** — Values exported after `apply` for humans or other automation.
- **State** — JSON mapping of resource addresses to real cloud IDs (`terraform.tfstate`).

## How Terraform fits in a workflow

```
Developer writes .tf  →  terraform init/plan/apply  →  Cloud API
                              ↓
                        terraform.tfstate (ID map)
```

Terraform does not run as a daemon. You invoke it deliberately. The CLI refreshes state from the API, builds a dependency graph, and proposes or executes changes.

## First configuration (Lab 01)

Open `labs/lab01-providers-init/main.tf`. Three layers appear: `terraform {}` (version and providers), `provider "aws" {}` (region only—no credentials), and `resource` / `output` blocks.

```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "random_pet" "lab_id" {
  length = 2
}

output "lab_id" {
  value = random_pet.lab_id.id
}
```

Lab 01 uses `random_pet` so you can practice `init`, `validate`, and `plan` without creating billable AWS resources.

## Version constraints

| Constraint | Meaning |
|------------|---------|
| `>= 1.5.0` | Terraform 1.5.0 or newer |
| `~> 5.0` | AWS provider 5.x (≥ 5.0, &lt; 6.0) |
| `~> 3.0` | Random provider 3.x |

After `terraform init`, `.terraform.lock.hcl` pins exact provider builds. Commit the lock file in team projects; add `.terraform/` to `.gitignore`.

## Authentication (AWS)

The AWS provider uses the standard SDK credential chain. Prefer a named profile—never embed keys in HCL.

```hcl
# Correct — region only; credentials from AWS_PROFILE or IAM role
provider "aws" {
  region = "us-east-1"
}
```

```bash
export AWS_PROFILE=training
aws sts get-caller-identity
```

## HCL reference syntax

- **Blocks:** `block_type "label" "name" { argument = value }`
- **References:** `random_pet.lab_id.id`, `var.aws_region`, `local.common_tags`
- **Collections:** lists `[]`, maps `{}`; strings use double quotes.

## Common mistakes

| Mistake | Fix |
|---------|-----|
| `validate` before `init` | Run `terraform init` first |
| Credentials in `provider` block | Use `AWS_PROFILE` or instance role |
| Mixing lab directories | `cd` into one lab folder only |
| Skipping `destroy` on AWS labs | Run `terraform destroy` after verify |
| Committing `.terraform/` | Commit lock file only |

## Operational commands (reference)

```bash
cd terraform/essentials/labs/lab01-providers-init
terraform init
terraform validate
terraform plan
terraform apply
terraform destroy
terraform version
```

---

## Hands-On Labs

Practice these concepts with guided lab exercises:

| Lab | Description |
|-----|-------------|
| [Lab 01: Providers and Init](../../labmanuals/lab01-providers-init.md) | `required_providers`, `init`, lock file, validate, plan |
| [Lab 02: EC2 Instance](../../labmanuals/lab02-ec2.md) | Data sources, security groups, first AWS resource |
