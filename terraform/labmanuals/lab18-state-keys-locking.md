# Lab 18 — State keys and locking

| | |
|---|---|
| **Goal** | Design a state key that marks a clear ownership boundary, then watch S3 locking stop a second apply from writing to that key at the same time. |
| **Time** | 40–50 minutes |
| **Tier** | Advanced |
| **Files** | `terraform/labs/lab18-state-keys-locking/` |

## Overview

Lab 17 put state in an S3 bucket, and `key` was just a path you copied. This lab treats that key
as the design decision it really is. The **state key** is the object path inside the bucket, and
it is the boundary of what one root module owns. Two modules pointed at the same key fight over
the same file; two modules with different keys cannot see or damage each other at all.

Because a key is shared by everyone who uses it, Terraform needs a way to stop two people writing
at once. A **lock** is a short-lived marker saying "an operation is in progress on this key".
With `use_lockfile = true` the marker is a small `.tflock` object beside the state, and a second
apply against the same key fails fast instead of corrupting the file. Keys and locking belong in
one lab because the key defines *what* is protected and the lock does the protecting. The module
computes its key from two variables so you can watch the convention change.

**A note on the expected output below.** The `validate` block and both output values were captured
from a real run. Blocks needing a real bucket are marked *(yours will differ)*, and the
lock-contention error in step 10 is Terraform's documented shape rather than a capture — the
exact wording varies between versions.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| S3 object at `labs/dev/network/terraform.tfstate` | State for this module, under a conventional key, in lab 17's bucket | Fractions of a cent |
| `terraform_data.key_design` | Computes the recommended key from `environment` and `component` | Free |
| `terraform_data.locking_note` | Carries the locking reminder through remote state | Free |

## Before you start

- [ ] [Lab 17 — S3 backend](lab17-s3-backend.md) completed, and **its S3 bucket still exists** — this lab writes to the same bucket and does not create one
- [ ] `TF_STATE_BUCKET` exported in every terminal you use here, holding the name you invented in lab 17
- [ ] Terraform 1.11.0 or newer, for generally-available `use_lockfile` (`terraform version`)
- [ ] AWS credentials exported and `aws sts get-caller-identity` working
- [ ] Two terminals available, both in this directory, for the locking drill
- [ ] Read [../docs/advanced/state.md](../docs/advanced/state.md)

**If you are starting at this lab, or opened a new terminal since lab 17**, re-export the bucket
name and confirm the bucket is really there before running anything else. `TF_STATE_BUCKET` is a
shell variable and does not survive a closed terminal.

```bash
export TF_STATE_BUCKET="tfstate-yourname-4821"   # your lab 17 name, not this placeholder
aws s3api get-bucket-versioning --bucket "$TF_STATE_BUCKET"
```

**Expected output**

```text
{
    "Status": "Enabled"
}
```

`NoSuchBucket` means the bucket does not exist — you have not done lab 17, or you deleted it. Run
[lab 17 steps 5 to 9](lab17-s3-backend.md#step-5--choose-a-globally-unique-bucket-name) to create
and version it, then return here. Nothing else in this lab requires lab 17's state object, only its
bucket.

`required_version` in this module is `>= 1.11.0` for the same reason as lab 17: `use_lockfile` is
only generally available from Terraform 1.11.

## Steps

### Step 1 — Read the key convention

The pattern is `labs/<environment>/<component>/terraform.tfstate`. Environment comes first so
one IAM policy can grant access to everything in `labs/dev/` and nothing in `labs/prod/`.

```bash
cd terraform/labs/lab18-state-keys-locking
grep -A3 'locals' main.tf
```

**Expected output**

```text
locals {
  recommended_key = "labs/${var.environment}/${var.component}/terraform.tfstate"
}
```

### Step 2 — Read the two variables that define the boundary

Each segment of the key is a separate input, because each names a separate axis of ownership:
which environment, and which component within it.

```bash
grep -A4 'variable' main.tf
```

**Expected output**

```text
variable "environment" {
  type        = string
  default     = "dev"
  description = "Environment segment of the state key, e.g. dev or staging."
}
--
variable "component" {
  type        = string
  default     = "network"
  description = "Component segment of the state key, e.g. network or app."
}
```

### Step 3 — Validate before touching AWS

```bash
terraform init -backend=false
terraform validate
```

**Expected output**

```text
Success! The configuration is valid.
```

### Step 4 — Point the backend at the conventional key

The `key` in `backend.hcl` must match the convention by hand. Terraform cannot use
`local.recommended_key` here, because backend blocks are read before expressions are evaluated —
the module can only *document* the key it expects, never supply it.

```bash
cp backend.hcl.example backend.hcl
# Edit backend.hcl: set bucket to your $TF_STATE_BUCKET name from lab 17 — the same bucket,
# a different key. Leave key as shipped.
cat backend.hcl
```

**Expected output** *(bucket will differ — it is your lab 17 name)*

```text
bucket       = "tfstate-yourname-4821"
key          = "labs/dev/network/terraform.tfstate"
region       = "us-east-1"
encrypt      = true
use_lockfile = true
```

### Step 5 — Initialize the remote backend

```bash
terraform init -backend-config=backend.hcl
```

**Expected output** *(yours will differ)*

```text
Initializing the backend...

Successfully configured the backend "s3"! Terraform will automatically
use this backend unless the backend configuration changes.

Terraform has been successfully initialized!
```

### Step 6 — Apply against the remote key

```bash
terraform apply -auto-approve
```

**Expected output** *(yours will differ)*

```text
Releasing state lock. This may take a few moments...

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

locking_note = "S3 lockfiles prevent concurrent state writes."
recommended_state_key = "labs/dev/network/terraform.tfstate"
```

`Releasing state lock` ends every remote operation. The matching `Acquiring state lock` line is
printed only when the acquire takes long enough to report — which is exactly what step 10 forces.

### Step 7 — Confirm both resources are in the remote state

```bash
terraform state list
```

**Expected output**

```text
terraform_data.key_design
terraform_data.locking_note
```

### Step 8 — Confirm the object landed at the conventional key

```bash
aws s3 ls "s3://$TF_STATE_BUCKET/labs/dev/network/"
```

**Expected output** *(timestamp and size will differ)*

```text
2026-08-29 12:14:52       1290 terraform.tfstate
```

Lab 17's object is still at `labs/lab17/` in the same bucket, untouched. Different keys, same
bucket, no interference — that is the whole point of the key boundary.

### Step 9 — Change the boundary and see the key move

A different environment or component is a different owner, so it gets a different key.

```bash
terraform apply -auto-approve -var=environment=staging -var=component=app
```

**Expected output** *(yours will differ)*

```text
  ~ resource "terraform_data" "key_design" {
      ~ input  = "labs/dev/network/terraform.tfstate" -> "labs/staging/app/terraform.tfstate"
    }

Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Outputs:

locking_note = "S3 lockfiles prevent concurrent state writes."
recommended_state_key = "labs/staging/app/terraform.tfstate"
```

The *recommended* key changed, but your state is still stored at the old key — the output is
advice, not configuration. Moving state to a new key is lab 19's job.

### Step 10 — Observe the lock stopping a second writer

In terminal 1, start an apply and leave the approval prompt open. While it waits, the lock is
held. Then run an apply in terminal 2.

```bash
# Terminal 1 — do not answer the prompt yet
terraform apply

# Terminal 2 — run this while terminal 1 is waiting
terraform apply
```

**Expected output** in terminal 2 *(documented shape; exact wording varies by version)*

```text
Error: Error acquiring the state lock

Lock Info:
  ID:        6a4e9f7c-...
  Path:      tfstate-yourname-4821/labs/dev/network/terraform.tfstate   # your bucket name here
  Operation: OperationTypeApply
  Who:       you@your-host
```

`Lock Info` always names the key and who holds it. Record the `ID` — the next step needs it.

### Step 11 — Release the lock the safe way

Answer `no` in terminal 1. Terraform releases the lock as it exits, and terminal 2 then succeeds
on a retry. This is the correct way out; step 12 is the wrong way, kept for when it is the only
way.

```bash
# Terminal 1: answer "no" at the prompt, then in terminal 2:
terraform apply -auto-approve
```

**Expected output** *(yours will differ)*

```text
Acquiring state lock. This may take a few moments...
Releasing state lock. This may take a few moments...

Apply complete! Resources: 0 added, 0 changed, 0 destroyed.
```

### Step 12 — Know when force-unlock is appropriate

`force-unlock` deletes the lock by hand. Only use it after confirming no apply is actually
running — usually when a CI job was killed mid-apply. Breaking a live lock is how state gets
corrupted, so it is a break-glass tool, not a routine fix. Do not run this now unless you have a
genuinely stuck lock.

```bash
terraform force-unlock 6a4e9f7c-...
```

**Expected output** *(yours will differ)*

```text
Terraform state has been successfully unlocked!
```

## Done when

- [ ] `recommended_state_key` printed `labs/dev/network/terraform.tfstate`
- [ ] `terraform state list` showed both `key_design` and `locking_note`
- [ ] The state object exists under `labs/dev/network/` in your bucket
- [ ] Overriding the two variables produced `labs/staging/app/terraform.tfstate`
- [ ] `Releasing state lock` appeared at the end of every remote operation
- [ ] Terminal 2 failed with `Error acquiring the state lock` naming your key
- [ ] Terminal 2 succeeded after terminal 1 released the lock, without force-unlock
- [ ] You can say what force-unlock risks and when it is justified

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `No valid credential sources found` | Credentials not exported in this shell | Re-export your keys; each terminal needs them |
| `NoSuchBucket` | Lab 17's bucket was deleted, or `bucket` in `backend.hcl` is the example placeholder | Recreate it with [lab 17 steps 5 to 9](lab17-s3-backend.md#step-5--choose-a-globally-unique-bucket-name), then set `bucket` to that name |
| `s3://` path resolves to `s3:///labs/...` | `TF_STATE_BUCKET` is unset in this terminal | Re-export it; see Before you start |
| `AccessDenied` on the new key prefix | Policy grants only the lab 17 prefix | A policy boundary, not a config error. Request access to `labs/*` |
| Second apply succeeds instead of failing | `use_lockfile` missing, or the two terminals use different keys | `grep use_lockfile backend.hcl` and confirm both `backend.hcl` files match |
| Lock persists after both terminals exit | An apply was killed before releasing it | Confirm nothing is running, then `terraform force-unlock <ID>` |
| `Local state cannot be unlocked by another process` | Ran the drill against local state, not S3 | Complete step 5 first; local backends do not take S3 locks |
| `Backend configuration changed` | `key` or `bucket` edited after init | `terraform init -reconfigure` |
| Plan wants to recreate everything | The key points at an empty or wrong object | Check `key` against the convention before applying |

## Cleanup

Destroy this lab's resources now. **Do not delete the bucket yet** — lab 19 migrates state into
the same bucket and deletes it at the end of the sequence.

```bash
terraform destroy -auto-approve
rm -f backend.hcl
rm -rf .terraform
```

[Lab 19](lab19-state-migration.md#cleanup) performs the bucket teardown, including the object
versions all three labs accumulated.

## Next steps

- Deep dive: [../docs/advanced/state.md](../docs/advanced/state.md)
- Visual: [../html/advanced.html](../html/advanced.html)
- Continue to [Lab 19 — State migration](lab19-state-migration.md)
