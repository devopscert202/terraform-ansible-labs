# Lab 01 — Providers and Initialization

| | |
|---|---|
| **Goal** | Configure version constraints for AWS and Random providers, initialize the working directory, and verify the configuration is valid. |
| **Time** | 20–30 minutes |
| **Difficulty** | Beginner |
| **Files** | `terraform/essentials/labs/lab01-providers-init/main.tf` |

## Overview

This lab introduces the `terraform` block, `required_providers`, and the initialization workflow. You will not create AWS resources — the configuration includes an AWS provider for credential-chain practice, but the only managed resource (if you apply) is a `random_pet` from the Random provider.

Initialization (`terraform init`) is the mandatory first step in every Terraform directory. It downloads provider plugins, writes the lock file, and prepares the backend. Skipping init is the number-one cause of "provider not found" errors for beginners.

## Learning objectives

After completing this lab you will be able to:

- Declare `required_version` and `required_providers` in HCL
- Explain why credentials never belong in a `provider` block
- Run `terraform init` and identify `.terraform.lock.hcl`
- List installed providers with `terraform providers`
- Run `terraform validate` and interpret success output

## Prerequisites checklist

- [ ] Terraform **1.5.0+** installed
- [ ] Terminal access to this repository
- [ ] (Optional) `AWS_PROFILE` set if you want to verify AWS credential chain — not required for validate/plan

## What you will build

| Artifact | Description |
|----------|-------------|
| `.terraform/` directory | Provider plugin cache (do not commit) |
| `.terraform.lock.hcl` | Pinned provider versions (commit in team projects) |
| Valid configuration | Passes `terraform validate` |
| (Optional) `random_pet.lab_id` | Created only if you run `apply` |

## Exercise index

| Exercise | Topic | Steps |
|----------|-------|-------|
| 1 | Verify toolchain | 1.1 – 1.2 |
| 2 | Inspect configuration | 2.1 – 2.2 |
| 3 | Initialize providers | 3.1 – 3.3 |
| 4 | Validate configuration | 4.1 |
| 5 | Optional apply/destroy | 5.1 – 5.2 |

---

## Exercise 1 — Verify toolchain

### Step 1.1 — Check Terraform version

Confirm the CLI meets the course minimum before working with lab files.

```bash
terraform version
```

**Validate:** Output includes `Terraform v1.5` or higher (e.g., `Terraform v1.5.7`).

**What happened:** The version constraint in `main.tf` requires `>= 1.5.0`. Older CLIs would refuse to run.

### Step 1.2 — Change to the lab directory

All Terraform commands in this lab run from the lab root module directory.

```bash
cd terraform/essentials/labs/lab01-providers-init
```

**Validate:** `pwd` ends with `lab01-providers-init`.

**What happened:** Each lab is an isolated root module with its own state. Running commands from the wrong directory uses the wrong state file.

---

## Exercise 2 — Inspect configuration

### Step 2.1 — Open main.tf

Read the file and locate three sections: `terraform`, `provider`, and `resource`/`output`.

```bash
cat main.tf
```

**Validate:** You see `hashicorp/aws` with `version = "~> 5.0"` and `hashicorp/random` with `version = "~> 3.0"`. No `access_key` or `secret_key` appears anywhere.

**What happened:** The `terraform` block declares provider requirements. The `provider "aws"` block sets only `region = "us-east-1"` — authentication uses the AWS credential chain (`AWS_PROFILE`, env vars, or IAM role).

### Step 2.2 — Note the random_pet resource

The `random_pet.lab_id` resource generates a friendly two-word identifier. It is safe for practice because it does not call AWS APIs.

**Validate:** Resource block shows `length = 2`.

**What happened:** `random_pet` is a managed resource. If you apply, Terraform stores its `id` in state.

---

## Exercise 3 — Initialize providers

### Step 3.1 — Run terraform init

Download and install provider plugins for this configuration.

```bash
terraform init
```

**Validate:** Final lines include:

```
Terraform has been successfully initialized!
```

**What happened:** Terraform read `required_providers`, downloaded AWS and Random provider binaries into `.terraform/providers/`, and created or updated `.terraform.lock.hcl`.

### Step 3.2 — Verify lock file exists

```bash
ls -la .terraform.lock.hcl
```

**Validate:** File exists with non-zero size.

**What happened:** The lock file records exact provider versions and checksums. Team members get identical plugins after `init`.

### Step 3.3 — List providers

```bash
terraform providers
```

**Validate:** Output includes both:

```
provider[registry.terraform.io/hashicorp/aws]
provider[registry.terraform.io/hashicorp/random]
```

**What happened:** `terraform providers` shows the dependency tree — root module directly requires both plugins.

---

## Exercise 4 — Validate configuration

### Step 4.1 — Run terraform validate

Static analysis of configuration structure and references.

```bash
terraform validate
```

**Validate:** Exact success message:

```
Success! The configuration is valid.
```

**What happened:** Validate checks syntax and internal references. It does not call AWS or create resources.

---

## Exercise 5 — Optional apply and destroy

Skip this exercise if your instructor only requires init/validate. No AWS resources are created.

### Step 5.1 — Preview with plan

```bash
terraform plan
```

**Validate:** Plan shows `1 to add` for `random_pet.lab_id` and `0 to change, 0 to destroy`.

**What happened:** Plan is read-only. It shows what apply would do.

### Step 5.2 — Apply and destroy

```bash
terraform apply
```

Type `yes` when prompted.

**Validate:** Output includes `lab_id = "` followed by two words (e.g., `happy-dog`).

```bash
terraform destroy
```

Type `yes`.

**Validate:** `Destroy complete! Resources: 0 added, 0 changed, 1 destroyed.`

**What happened:** Apply created the pet in state; destroy removed it.

---

## Done when

- [ ] `terraform version` shows 1.5+
- [ ] `terraform init` completed successfully
- [ ] `.terraform.lock.hcl` exists
- [ ] `terraform providers` lists aws and random
- [ ] `terraform validate` reports success
- [ ] (If applied) `terraform destroy` completed

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `terraform: command not found` | CLI not installed | Install Terraform 1.5+ from hashicorp.com |
| `Unsupported Terraform Core version` | CLI too old | Upgrade Terraform |
| `Could not load plugin` | init not run | Run `terraform init` |
| `terraform validate` fails before init | Providers missing | Run `terraform init` first |
| Network timeout during init | Firewall/proxy | Check network; retry init |
| Permission denied on `.terraform/` | File ownership | Fix permissions or remove `.terraform/` and re-init |

## Cleanup

If you ran apply:

```bash
terraform destroy
```

Remove local plugin cache (optional — saves disk space):

```bash
rm -rf .terraform/
```

Do **not** delete `.terraform.lock.hcl` if this is a shared project — teammates need it.

## Key takeaways

1. **`terraform init`** is required after clone or provider changes.
2. **Never put credentials** in `provider` blocks — use `AWS_PROFILE`.
3. The **lock file** ensures reproducible provider versions.
4. **`terraform validate`** is a fast pre-flight check before plan.
5. Each lab directory is a **separate root module** with isolated state.

## Next steps

- Read [docs/02-providers/README.md](../docs/02-providers/README.md)
- Open [html/foundations.html](../html/foundations.html)
- Continue to [Lab 02 — EC2](lab02-ec2.md)
