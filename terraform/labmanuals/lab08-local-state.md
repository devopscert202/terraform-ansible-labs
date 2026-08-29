# Lab 08 — Local State

| | |
|---|---|
| **Goal** | Inspect the local `terraform.tfstate` file, list and show resources with the state commands, and confirm that state stores secrets as plain text. |
| **Time** | 40–50 minutes |
| **Tier** | Intermediate |
| **Files** | `terraform/labs/lab08-local-state/` |

## Overview

Every `apply` you have run wrote a file called `terraform.tfstate`. **State** is Terraform's record
of what it created: one entry per resource, holding the real ID AWS handed back and every attribute
value. It is how Terraform knows on the next run whether to create, change, or leave a resource
alone. Without state, Terraform would create a duplicate every time.

Because there is no `backend` block in this configuration, state is a JSON file sitting in the lab
directory. That is fine for one person on one laptop and wrong for a team, for two reasons you will
prove here: the file is easy to lose, and anything sensitive inside it is in plain text. Tier 3
fixes both by moving state to S3.

This lab uses the `random` provider, so it creates nothing in AWS and costs nothing. The generated
values differ on every run, so your pet name and password will not match the examples below.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `random_pet.server` | A generated name, standing in for a real server | Free |
| `random_password.db` | A generated 16-character secret | Free |
| `terraform.tfstate` | The local state file you will inspect | Free |

## Before you start

- [ ] Lab 07 completed ([lab07-tfvars-secrets.md](lab07-tfvars-secrets.md)), where you saw that
  `sensitive = true` hides a value on screen but does not encrypt it
- [ ] `python3` available, for reading the state file's JSON structure in Step 11
- [ ] Working directory: `../labs/lab08-local-state/` (no AWS credentials needed)

## Steps

### Step 1 — Confirm no state exists yet

```bash
cd terraform/labs/lab08-local-state
ls
```

**Expected output**

```text
main.tf
outputs.tf
```

Two files, no state. Terraform creates the state file on the first `apply`, not on `init`.

### Step 2 — Note the absence of a backend block

```bash
head -12 main.tf
```

**Expected output**

```text
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# There is no backend block, so Terraform writes state to ./terraform.tfstate.
resource "random_pet" "server" {
```

A `backend` block tells Terraform where to keep state. There is none here, which means the default:
a local file named `terraform.tfstate` in the current directory.

### Step 3 — Initialize

```bash
terraform init
```

**Expected output**

```text
Terraform has been successfully initialized!
```

### Step 4 — Apply

```bash
terraform apply -auto-approve
```

**Expected output**

```text
random_pet.server: Creation complete after 0s [id=lab08-blessed-colt]
random_password.db: Creation complete after 1s [id=none]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

db_password = <sensitive>
server_name = "lab08-blessed-colt"
```

`random_password.db` reports `id=none` on purpose — that provider does not expose a meaningful ID.
The value it generated is in the `result` attribute, which you will find in Step 12.

### Step 5 — Find the state file

```bash
ls -l terraform.tfstate
```

**Expected output**

```text
-rw-r--r--@ 1 you  staff  2044 29 Aug 12:33 terraform.tfstate
```

The file now exists, roughly two kilobytes of JSON. Never edit it by hand — hand edits are how you
get a state file that disagrees with reality.

### Step 6 — List what state is tracking

```bash
terraform state list
```

**Expected output**

```text
random_password.db
random_pet.server
```

Each line is a **resource address** — the `type.name` pair you wrote in your configuration.
Addresses are how you refer to one specific resource in every state command.

### Step 7 — Show one resource's recorded attributes

```bash
terraform state show random_pet.server
```

**Expected output**

```text
# random_pet.server:
resource "random_pet" "server" {
    id        = "lab08-blessed-colt"
    length    = 2
    prefix    = "lab08"
    separator = "-"
}
```

You wrote `length` and `prefix`. Terraform recorded those plus `id` and `separator`, which it
learned from the provider. That full picture is what makes the next `plan` accurate.

### Step 8 — Show the resource that holds a secret

```bash
terraform state show random_password.db
```

**Expected output**

```text
# random_password.db:
resource "random_password" "db" {
    bcrypt_hash = (sensitive value)
    id          = "none"
    length      = 16
    lower       = true
    min_lower   = 0
    min_numeric = 0
    min_special = 0
    min_upper   = 0
    number      = true
    numeric     = true
    result      = (sensitive value)
    special     = false
    upper       = true
}
```

The provider marked `result` and `bcrypt_hash` as sensitive, so the CLI prints `(sensitive value)`.
Remember this screen — Step 12 reads the same attribute from the file underneath it.

### Step 9 — Show the whole state at once

```bash
terraform show
```

**Expected output**

```text
# random_password.db:
resource "random_password" "db" {
...
}

# random_pet.server:
resource "random_pet" "server" {
...
}


Outputs:

db_password = (sensitive value)
server_name = "lab08-blessed-colt"
```

`terraform show` prints every tracked resource and then every output. Use it to see the whole
picture; use `state show` when you want one resource.

### Step 10 — Read outputs, and watch the redaction come off

```bash
terraform output
terraform output db_password
terraform output -raw db_password
```

**Expected output**

```text
db_password = <sensitive>
"FqUv7nxAhvAG9mnz"
FqUv7nxAhvAG9mnz
```

Three different renderings of the same stored value. Listing all outputs redacts it. Asking for it
by name prints it with quotes, and `-raw` prints it bare. Redaction is a guard against accidental
display, not a permission boundary — if you ask directly, you get the secret.

### Step 11 — Look at the state file's structure

```bash
python3 -c "import json; d=json.load(open('terraform.tfstate')); print('version', d['version']); print('serial', d['serial']); print('resources', [r['type']+'.'+r['name'] for r in d['resources']])"
```

**Expected output**

```text
version 4
serial 3
resources ['random_password.db', 'random_pet.server']
```

State is ordinary JSON with a documented shape. `version` is the state format version, `serial`
increments on every write, and `resources` is the list you saw in Step 6. Terraform uses `serial`
and a `lineage` field to detect that two people have written the same state — the problem a remote
backend with locking exists to prevent.

### Step 12 — Read the secret straight out of the state file

```bash
grep -o '"result": "[^"]*"' terraform.tfstate
```

**Expected output**

```text
"result": "FqUv7nxAhvAG9mnz"
```

This is the lesson the whole lab exists for. Step 8 showed this attribute as `(sensitive value)`;
the redaction is a display convenience in the CLI. In the file, the generated password is stored in
clear text. Anyone who can read the file can read the secret, which is why a local state file must
never be committed to git and why Tier 3 moves state into encrypted remote storage.

### Step 13 — Prove state prevents duplicate creation

```bash
terraform plan
```

**Expected output**

```text
No changes. Your infrastructure matches the configuration.

Terraform has compared your real infrastructure against your configuration
and found no differences, so no changes are needed.
```

Terraform compared the configuration against state, found them identical, and proposed nothing.
Delete `terraform.tfstate` and this same plan would offer to create both resources again — which is
why losing the file is a real incident.

### Step 14 — Destroy, and see what state looks like afterwards

```bash
terraform destroy -auto-approve
ls
terraform state list
```

**Expected output**

```text
Destroy complete! Resources: 2 destroyed.
main.tf
outputs.tf
terraform.tfstate
terraform.tfstate.backup
```

`terraform state list` prints nothing, because state now tracks zero resources. Note that
`terraform.tfstate` was not deleted — it still exists, emptied — and a `terraform.tfstate.backup`
now holds the previous version. Both are gitignored in this repository.

## Done when

- [ ] `terraform.tfstate` exists after `apply` and did not exist before
- [ ] `terraform state list` shows both resource addresses
- [ ] `terraform state show random_pet.server` prints the recorded attributes
- [ ] `state show random_password.db` shows `result = (sensitive value)`
- [ ] `terraform output -raw db_password` prints the secret in the clear
- [ ] You located that same password in plain text inside `terraform.tfstate`
- [ ] `terraform plan` reports `No changes`
- [ ] After `destroy`, `state list` is empty but the state file remains

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `No state file was found` | `apply` has not run yet in this directory | Run `terraform apply` |
| `Invalid resource address` | Typo in the address | Copy the exact line from `terraform state list` |
| `grep` finds nothing | Apply did not complete, or you are in the wrong directory | `pwd`, then `ls -l terraform.tfstate` |
| `KeyError: 'resources'` in Step 11 | State has no resources yet, or was destroyed first | Re-run `terraform apply` before Step 11 |
| Plan wants to create both resources again | State file deleted or you are in another directory | `pwd`, and confirm the state file is present |
| `Provider configuration not present` | `.terraform` cache removed | Run `terraform init` again |

## Cleanup

```bash
terraform destroy -auto-approve
```

## Next steps

- Deep dive: [docs/intermediate/07-state.md](../docs/intermediate/07-state.md)
- Visual: [html/intermediate.html](../html/intermediate.html)
- Continue to [Lab 09 — Modules](lab09-modules.md)
