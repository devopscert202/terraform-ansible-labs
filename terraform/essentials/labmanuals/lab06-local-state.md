# Lab 06 — Local State

> **Goal:** Understand Terraform's default **local backend** by creating a resource, inspecting `terraform.tfstate`, and correlating state contents with CLI output.
> **Time:** ~45 min · **Difficulty:** Beginner · **Files:** `labs/lab06-local-state/`

## Overview

Terraform's job is to keep **real infrastructure** aligned with **desired configuration**. The bridge is **state** — a JSON record of managed resource metadata. When no `backend` block is configured, Terraform stores state in a local file named `terraform.tfstate` in the working directory.

This lab creates a harmless `random_pet` resource, applies it, and inspects state with `terraform state list`, `terraform show`, and direct file reads. You will learn why state files are sensitive, why they must not be committed to git, and how destroy clears managed objects from state.

No cloud credentials are required.

## Learning objectives

- Explain what the local backend does when no `backend` block exists
- Correlate `terraform output` values with `terraform show` and `terraform.tfstate`
- Use `terraform state list` and `terraform state show` for targeted inspection
- Treat `terraform.tfstate` as sensitive operational data
- Destroy resources and confirm state returns to empty

## Prerequisites

- [ ] Terraform 1.5+ installed (`terraform version`)
- [ ] Lab 03 complete (plan/apply/destroy workflow)
- [ ] `jq` installed (optional, for JSON parsing)
- [ ] Working directory: `terraform/essentials/labs/lab06-local-state`

## What you will build

```
terraform/essentials/labs/lab06-local-state/
├── main.tf                  # random_pet, output (no backend block)
├── terraform.tfstate        # created by apply — DO NOT COMMIT
└── .terraform/              # provider cache
```

```
  terraform apply
       │
       ▼
  terraform.tfstate  ◄────  random_pet.first (id, attributes)
       │
       ▼
  terraform show / state list / cat terraform.tfstate
```

---

## Exercise 1 — Read the configuration

<a id="ex1"></a>

### Step 1.1 — Navigate to the lab directory

```bash
cd ~/terraform-ansible-labs/terraform/essentials/labs/lab06-local-state
```

**Validate**

```bash
pwd
```

```text
.../terraform/essentials/labs/lab06-local-state
```

**What happened:** This isolated root module deliberately omits a `backend` block to demonstrate default local state behavior.

### Step 1.2 — Display main.tf

```bash
cat main.tf
```

**Validate** — file contains:

```hcl
# No backend block means Terraform uses local terraform.tfstate.
resource "random_pet" "first" {
  prefix = "state-lab"
  length = 2
}

output "first_resource" {
  value = random_pet.first.id
}
```

No `backend "s3"` or `backend "azurerm"` block present.

**What happened:** Absence of a backend block is equivalent to `backend "local"` with default path `terraform.tfstate`.

### Step 1.3 — Confirm no existing state file

```bash
ls terraform.tfstate 2>&1
```

**Validate**

```text
ls: terraform.tfstate: No such file or directory
```

Or file absent if you destroyed in a previous run.

**What happened:** First-time apply creates `terraform.tfstate`. Starting clean proves the file is Terraform-generated.

---

## Exercise 2 — Initialize and apply

<a id="ex2"></a>

### Step 2.1 — Run terraform init

```bash
terraform init
```

**Validate**

```text
Terraform has been successfully initialized!
```

**What happened:** Even state-focused labs need `init` to install the Random provider.

### Step 2.2 — Validate configuration

```bash
terraform validate
```

**Validate**

```text
Success! The configuration is valid.
```

**What happened:** Validation does not create state — only checks configuration consistency.

### Step 2.3 — Apply with auto-approve

```bash
terraform apply -auto-approve
```

**Validate**

```text
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
```

And output `first_resource` shows a value like `state-lab-happy-dog`.

**What happened:** Apply created `random_pet.first` and wrote a new `terraform.tfstate` file recording the resource ID and attributes.

---

## Exercise 3 — Inspect state with CLI commands

<a id="ex3"></a>

### Step 3.1 — List managed resources

```bash
terraform state list
```

**Validate**

```text
random_pet.first
```

Exactly one address.

**What happened:** `state list` reads the state file and prints resource addresses. This is the quickest inventory of managed infrastructure.

### Step 3.2 — Show human-readable state

```bash
terraform show
```

**Validate** — output includes:

```text
# random_pet.first:
resource "random_pet" "first" {
    id     = "state-lab-happy-dog"
    length = 2
    prefix = "state-lab"
}
```

The `id` must match `terraform output first_resource`.

**What happened:** `terraform show` renders current state as HCL. It is the primary human-readable view of what Terraform tracks.

### Step 3.3 — Show a single resource address

```bash
terraform state show random_pet.first
```

**Validate** — displays attributes for `random_pet.first` only, including `id` matching your output.

**What happened:** Targeted inspection scales better than full `show` in modules with dozens of resources.

### Step 3.4 — Compare output to state

```bash
terraform output -raw first_resource
```

**Validate** — value equals the `id` attribute in `terraform state show random_pet.first`.

**What happened:** Outputs are convenience views; state is authoritative. They should agree after a successful apply.

---

## Exercise 4 — Inspect terraform.tfstate directly

<a id="ex4"></a>

### Step 4.1 — Confirm state file exists

```bash
ls -la terraform.tfstate
```

**Validate**

```text
-rw-r--r--  1 user  staff  ... terraform.tfstate
```

Non-zero file size (typically a few KB).

**What happened:** Local backend persists state as JSON on disk. Remote backends (S3, Terraform Cloud) store the same data structure remotely.

### Step 4.2 — View state file structure with jq

```bash
jq '.resources[].type' terraform.tfstate
```

**Validate**

```text
"random_pet"
```

**What happened:** State JSON contains version, serial, lineage, and a `resources` array. Each entry records type, name, provider, and instances.

### Step 4.3 — Extract the pet ID from raw state

```bash
jq -r '.resources[] | select(.type=="random_pet") | .instances[0].attributes.id' terraform.tfstate
```

**Validate**

```text
state-lab-happy-dog
```

Matches CLI output.

**What happened:** Direct state reads are useful for debugging but dangerous in production — state may contain sensitive values even when outputs are marked sensitive.

---

## Exercise 5 — Understand state sensitivity

<a id="ex5"></a>

### Step 5.1 — Check git ignore patterns (repository level)

```bash
grep -r tfstate ~/terraform-ansible-labs/.gitignore 2>/dev/null || grep tfstate ~/terraform-ansible-labs/terraform/essentials/labs/.gitignore 2>/dev/null || echo "Verify tfstate is gitignored in your org"
```

**Validate** — `terraform.tfstate` or `*.tfstate` appears in ignore rules, or your instructor confirms the policy.

**What happened:** Committing state leaks resource metadata and sometimes secrets. Teams use remote backends with encryption and locking instead.

### Step 5.2 — Observe backup file after apply

```bash
ls -la terraform.tfstate*
```

**Validate** — may include `terraform.tfstate.backup` from previous operations.

**What happened:** Terraform writes a backup before state mutations. Treat backups as equally sensitive.

---

## Exercise 6 — Destroy and verify empty state

<a id="ex6"></a>

### Step 6.1 — Run plan with no configuration changes

```bash
terraform plan
```

**Validate**

```text
No changes. Your infrastructure matches the configuration.
```

**What happened:** Steady-state plans with no drift are what operators want before any change window.

### Step 6.2 — Destroy all resources

```bash
terraform destroy -auto-approve
```

**Validate**

```text
Destroy complete! Resources: 1 destroyed.
```

**What happened:** Terraform removed `random_pet.first` from state. The pet ID value is gone permanently.

### Step 6.3 — Confirm empty state list

```bash
terraform state list
```

**Validate** — no output.

**What happened:** Empty state means Terraform manages zero resources. The `terraform.tfstate` file may still exist but contain no resources.

### Step 6.4 — Inspect state file after destroy

```bash
jq '.resources | length' terraform.tfstate
```

**Validate**

```text
0
```

**What happened:** Post-destroy state retains metadata (serial, lineage) but the resources array is empty.

---

## Key takeaways

- No `backend` block → local `terraform.tfstate` in the working directory
- State is the source of truth for what Terraform manages — not the `.tf` files alone
- `terraform show` and `state show` are safer than sharing raw JSON
- State files are **sensitive** — never commit them; prefer remote backends in teams
- `serial` and `lineage` help detect concurrent writes and state corruption

## Done when

- [ ] `terraform apply` created `random_pet.first`
- [ ] `terraform state list` showed `random_pet.first`
- [ ] `terraform show` id matched `terraform output first_resource`
- [ ] `terraform.tfstate` exists and contains `random_pet` in JSON
- [ ] You can explain why state must not be committed
- [ ] `terraform destroy` completed and `terraform state list` is empty

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `terraform.tfstate` not created | Apply did not succeed | Re-run `terraform apply` and read errors |
| `state list` empty after apply | Wrong working directory | `cd` to lab06 directory |
| `jq: command not found` | jq not installed | Use `terraform show` instead, or install jq |
| Output id differs from state | Partial apply or stale shell | Re-run `terraform refresh` then compare |
| `state show` says resource not found | Typo in address | Use exact name from `state list` |
| Cannot destroy | State already empty | Run `terraform apply` first to recreate |

## Cleanup

```bash
cd ~/terraform-ansible-labs/terraform/essentials/labs/lab06-local-state
terraform destroy -auto-approve 2>/dev/null || true
rm -f terraform.tfstate terraform.tfstate.backup main.tf.bak
```

Verify `terraform state list` produces no output.

## Next steps

- [Lab 07 — Simple module](lab07-simple-module.md)
- [State fundamentals (interactive HTML)](../html/state.html)
- [State doc](../docs/03-state/README.md)

---
*Source: Terraform Essentials bootcamp · L9 AP-01 · Next: [lab07](lab07-simple-module.md)*
