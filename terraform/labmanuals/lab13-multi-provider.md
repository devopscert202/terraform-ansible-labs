# Lab 13 — Multi-provider configuration

| | |
|---|---|
| **Goal** | Run one root module that loads two providers at once and read an output that combines a value from each. |
| **Time** | 20–25 minutes |
| **Tier** | Advanced |
| **Files** | `terraform/labs/lab13-multi-provider/` |

## Overview

A **provider** is the plugin Terraform uses to talk to one particular platform — `aws` talks to
AWS, `random` generates random values locally. Every lab so far has used providers, but always
one at a time. Real modules routinely load several, because one stack often needs an AWS
resource, a random suffix, and a TLS certificate together.

This lab declares both `hashicorp/aws` and `hashicorp/random` in a single module. Terraform
configures both, but only `random` creates something — showing that a provider can be ready
without owning any resource, and letting you practise the mechanics without spending money.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `random_pet.label` | A two-word name generated locally, proving the `random` provider works | Free |
| `provider "aws"` (configured, unused) | Sets the `us-east-2` region context and validates the plugin loads | Free |
| Output `provider_composition` | A map combining the AWS region and the generated label | Free |

Nothing in this lab touches your AWS account, so it applies cleanly even with no credentials
exported.

## Before you start

- [ ] [Lab 12 — Functions](lab12-functions.md) completed
- [ ] Terraform 1.5.0 or newer on your `PATH` (`terraform version`)
- [ ] Network access to `registry.terraform.io` so `init` can download plugins
- [ ] Read the module layout notes in [../docs/10-multi-provider.md](../docs/10-multi-provider.md)

## Steps

### Step 1 — Move into the lab directory

```bash
cd terraform/labs/lab13-multi-provider
ls
```

**Expected output**

```text
main.tf
terraform.tfvars.example
variables.tf
```

### Step 2 — Read the provider version constraints

`required_providers` names every plugin the module needs and pins an acceptable version range
for each. `~> 5.0` means "any 5.x, but not 6.0" — bug fixes are allowed, a breaking major
upgrade is not.

```bash
grep -A6 required_providers main.tf
```

**Expected output**

```text
  required_providers {
    aws    = { source = "hashicorp/aws", version = "~> 5.0" }
    random = { source = "hashicorp/random", version = "~> 3.0" }
  }
}
```

### Step 3 — Note that each provider is configured separately

Declaring a plugin and configuring it are two different things. `aws` needs a region; `random`
needs nothing, so its block is empty — but declaring it still documents the dependency for the
next person reading the module.

```bash
grep -n '^provider' main.tf
```

**Expected output**

```text
9:provider "aws" { region = var.aws_region }
10:provider "random" {}
```

### Step 4 — Inspect the region variable

`aws_region` is the module's only input, and the only thing the AWS provider needs.

```bash
cat variables.tf
```

**Expected output**

```text
variable "aws_region" {
  type        = string
  default     = "us-east-2"
  description = "AWS region used by the AWS provider."
}
```

### Step 5 — Review the output that spans both providers

This single output is the point of the lab: one value comes from the AWS provider's
configuration, the other from a resource the `random` provider created.

```bash
grep -A3 'output "provider_composition"' main.tf
```

**Expected output**

```text
output "provider_composition" {
  value = { aws_region = var.aws_region, generated_label = random_pet.label.id }
}
```

### Step 6 — Check the formatting

`-check` reports badly formatted files without rewriting them, and exits non-zero if any are
found. It prints nothing when everything is already canonical.

```bash
terraform fmt -check
echo "exit=$?"
```

**Expected output**

```text
exit=0
```

### Step 7 — Download both plugins

```bash
terraform init
```

**Expected output**

```text
Initializing provider plugins...
- Finding hashicorp/random versions matching "~> 3.0"...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/random v3.9.0...
- Installed hashicorp/random v3.9.0 (signed by HashiCorp)
- Installing hashicorp/aws v5.100.0...
- Installed hashicorp/aws v5.100.0 (signed by HashiCorp)

Terraform has been successfully initialized!
```

Your patch versions may differ; only the `5.x` and `3.x` majors are guaranteed by the pins.

### Step 8 — Inspect the lock file

`init` writes `.terraform.lock.hcl` recording the exact versions and checksums it chose. Commit
this file so every teammate and CI run installs byte-identical plugins.

```bash
grep provider .terraform.lock.hcl
```

**Expected output**

```text
provider "registry.terraform.io/hashicorp/aws" {
provider "registry.terraform.io/hashicorp/random" {
```

### Step 9 — Validate the configuration

```bash
terraform validate
```

**Expected output**

```text
Success! The configuration is valid.
```

### Step 10 — Plan the change

Read the plan before applying. Note that only `random_pet` appears — the AWS provider is loaded
and configured but owns nothing, so it contributes no actions.

```bash
terraform plan
```

**Expected output**

```text
Terraform will perform the following actions:

  # random_pet.label will be created
  + resource "random_pet" "label" {
      + id        = (known after apply)
      + length    = 2
      + separator = "-"
    }

Plan: 1 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + provider_composition = {
      + aws_region      = "us-east-2"
      + generated_label = (known after apply)
    }
```

`aws_region` is already known because it comes from a variable; `generated_label` is
`(known after apply)` because the value does not exist until the resource is created.

### Step 11 — Apply and read the combined output

```bash
terraform apply -auto-approve
```

**Expected output**

```text
Plan: 1 to add, 0 to change, 0 to destroy.

random_pet.label: Creating...
random_pet.label: Creation complete after 0s [id=distinct-dolphin]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

provider_composition = {
  "aws_region" = "us-east-2"
  "generated_label" = "distinct-dolphin"
}
```

Your `generated_label` will be a different two-word pair — the value is random.

### Step 12 — Confirm only one resource exists in state

```bash
terraform state list
terraform state show random_pet.label
```

**Expected output**

```text
random_pet.label
# random_pet.label:
resource "random_pet" "label" {
    id        = "distinct-dolphin"
    length    = 2
    separator = "-"
}
```

The configured-but-unused AWS provider contributes nothing to state, which is why the list has a
single entry.

### Step 13 — Override the region without editing any file

`-var` supplies a value on the command line. The composed output changes even though the AWS
provider still creates nothing.

```bash
terraform plan -var='aws_region=us-east-1'
```

**Expected output**

```text
Changes to Outputs:
  ~ provider_composition = {
      ~ aws_region      = "us-east-2" -> "us-east-1"
        # (1 unchanged attribute hidden)
    }
```

The marker is `~`, not `+`: step 11 already applied this output, so Terraform is showing a change
to a value it holds in state rather than a new one. The hidden attribute is `generated_label`,
unchanged because `random_pet.label` is not being replaced.

## Done when

- [ ] `terraform init` reported installing both `hashicorp/aws` and `hashicorp/random`
- [ ] `.terraform.lock.hcl` exists and names both providers
- [ ] `terraform plan` showed exactly one resource to add
- [ ] `provider_composition` shows `us-east-2` plus a two-word generated label
- [ ] `terraform state list` returns exactly `random_pet.label`
- [ ] Overriding `aws_region` changed the output without changing the plan's resource count

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `Failed to query available provider packages` | No network route to the Terraform registry | Check proxy settings, then rerun `terraform init` |
| `Could not retrieve the list of available versions` | Version pin cannot be satisfied | Confirm the `~> 5.0` and `~> 3.0` constraints are unchanged in `main.tf` |
| `Error: Inconsistent dependency lock file` | Lock file predates a constraint edit | Run `terraform init -upgrade` |
| `Provider configuration not present` | A `provider` block was deleted but is still referenced | Restore both `provider` blocks from `main.tf` |
| `terraform fmt -check` exits 3 | A file is not canonically formatted | Run `terraform fmt` to rewrite it, then re-check |
| Apply asks for AWS credentials | An AWS resource was added to the module | This lab creates no AWS resources; revert local edits to `main.tf` |

## Cleanup

```bash
terraform destroy -auto-approve
```

## Next steps

- Deep dive: [../docs/10-multi-provider.md](../docs/10-multi-provider.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab13-multi-provider)
- Continue to [Lab 14 — local-exec provisioner](lab14-local-exec-provisioner.md)
