# Lab 01 — Providers and Initialization

| | |
|---|---|
| **Goal** | Declare which providers and Terraform version a configuration needs, initialize the directory, and read the lock file that `init` creates. |
| **Time** | 20–30 minutes |
| **Tier** | Basic |
| **Files** | `../labs/lab01-providers-init/` |

## Overview

A **provider** is a plugin that teaches Terraform how to talk to one particular service. The
`aws` provider knows how to create EC2 instances; the `random` provider only invents random
values. Terraform ships with none of them built in, so every configuration must state which
providers it needs and which versions are acceptable.

`terraform init` reads those requirements and downloads the plugins. It is the first command you
run in any new directory, and forgetting it is the most common beginner error. This lab runs it
on a configuration whose only resource is a random two-word name, so you can practise safely.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `terraform` block | Declares the minimum Terraform version and required providers | None |
| `.terraform/` directory | Where `init` stores the downloaded plugins | None |
| `.terraform.lock.hcl` | Records the exact plugin versions `init` chose | None |
| `random_pet.lab_id` | A throwaway two-word name, created only if you apply | None |

## Before you start

- [ ] [Lab 00](lab00-aws-setup-and-init.md) completed — your credentials work and `init` succeeded once
- [ ] A terminal open at the root of this repository

## Steps

### Step 1 — Move into the lab directory

Terraform always acts on the directory you are standing in, and each lab is self-contained, so
running a command from the wrong folder uses the wrong configuration.

```bash
cd terraform/labs/lab01-providers-init
```

### Step 2 — Read the requirements block

```bash
cat main.tf
```

The top of the file declares what this configuration needs:

```hcl
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

`required_version` refuses to run on a Terraform older than 1.5.0. `source` is the plugin's
address in the public registry. `version = "~> 5.0"` means "any 5.x release, but never 6.0" —
a new major version may change behaviour, so it is held back deliberately.

Note what is absent: no access key and no secret key. Credentials stay in your environment,
exactly as you set them up in Lab 00.

### Step 3 — Initialize the directory

```bash
terraform init
```

**Expected output**

```text
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Finding hashicorp/random versions matching "~> 3.0"...
- Installing hashicorp/random v3.9.0...
- Installing hashicorp/aws v5.100.0...

Terraform has been successfully initialized!
```

Terraform picked the newest version allowed by each constraint and downloaded it.

### Step 4 — Check what init created

```bash
ls -a
```

**Expected output**

```text
.		..		.terraform	.terraform.lock.hcl	main.tf
```

`.terraform/` holds the plugin binaries and is disposable — delete it and re-run `init` to
rebuild it. `.terraform.lock.hcl` is the opposite: it pins the exact versions so everyone on a
team installs identical plugins. Commit the lock file; never commit `.terraform/`.

### Step 5 — List the required providers

```bash
terraform providers
```

**Expected output**

```text
Providers required by configuration:
.
├── provider[registry.terraform.io/hashicorp/aws] ~> 5.0
└── provider[registry.terraform.io/hashicorp/random] ~> 3.0
```

### Step 6 — Validate the configuration

`terraform validate` checks the file for syntax errors and references to things that do not
exist. It reads only local files, calls no cloud API, and costs nothing.

```bash
terraform validate
```

**Expected output**

```text
Success! The configuration is valid.
```

### Step 7 — Preview what apply would do

```bash
terraform plan
```

**Expected output**

```text
  # random_pet.lab_id will be created
  + resource "random_pet" "lab_id" {
      + id        = (known after apply)
      + length    = 2
      + separator = "-"
    }

Plan: 1 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + lab_id = (known after apply)
```

`plan` reports without changing anything, so it is always safe to run.

### Step 8 — Create the random name

`apply` makes reality match your configuration. Here that means a two-word name from the random
provider — nothing in AWS, nothing billable. Terraform reprints the plan and waits; type `yes`.

```bash
terraform apply
```

**Expected output**

```text
random_pet.lab_id: Creating...
random_pet.lab_id: Creation complete after 0s [id=classic-fox]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

lab_id = "classic-fox"
```

Your two words will differ.

### Step 9 — Remove it again

```bash
terraform destroy
```

Terraform lists what it will remove and waits. Type `yes`.

**Expected output**

```text
random_pet.lab_id: Destroying... [id=classic-fox]
random_pet.lab_id: Destruction complete after 0s

Destroy complete! Resources: 1 destroyed.
```

## Done when

- [ ] `terraform init` printed `Terraform has been successfully initialized!`
- [ ] `.terraform.lock.hcl` exists in the lab directory
- [ ] `terraform providers` listed both `aws` and `random`
- [ ] `terraform validate` reported success
- [ ] `terraform plan` showed `1 to add`
- [ ] `terraform destroy` reported `1 destroyed`

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `Could not load plugin` | `init` not run in this directory | Run `terraform init` |
| `Unsupported Terraform Core version` | Terraform older than 1.5.0 | Upgrade Terraform |
| `validate` fails before `init` | Provider schemas not downloaded yet | Run `terraform init` first |
| `Failed to install provider` | No network route to the registry | Check proxy or firewall, retry `init` |
| `No such file or directory` from `cat main.tf` | Wrong directory | `cd terraform/labs/lab01-providers-init` |

## Cleanup

```bash
terraform destroy
```

Deleting `.terraform/` is optional and only frees disk space. Leave `.terraform.lock.hcl` alone —
in a shared project your teammates need it.

## Next steps

- Deep dive: [Providers](../docs/01-providers.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab01-providers-init)
- Continue to [Lab 02 — Building a Network by Hand in the Console](lab02-console-vpc.md)
