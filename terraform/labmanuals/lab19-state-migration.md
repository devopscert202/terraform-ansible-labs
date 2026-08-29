# Lab 19 — State migration

| | |
|---|---|
| **Goal** | Move a module's existing state from a local file into an S3 backend without Terraform recreating anything, and prove it by getting a plan with no changes. |
| **Time** | 40–50 minutes |
| **Tier** | Advanced |
| **Files** | `terraform/labs/lab19-state-migration/` |

## Overview

Labs 17 and 18 started with S3. Real projects almost never do — they start local, grow, and then
someone must move the state to a shared backend without disturbing running infrastructure. That
move is **state migration**.

Migration copies the state *file* and changes nothing in AWS. Your resources are not touched,
recreated, or restarted — Terraform simply reads and writes the same records from a new place.
You confirm it worked with a plan reporting **no changes**, meaning the new state still matches
reality. If a post-migration plan instead wants to create everything from scratch, the copy did
not happen and Terraform is reading an empty state. That is recoverable only from a backup,
which is why this lab makes you take one first.

**A note on the expected output below.** Everything through step 4 was captured from a real local
run, as were the S3 blocks and every command in the Cleanup section. Values unique to your account
— bucket name, version ids, sizes, timestamps — are marked *(yours will differ)*. The migration
prompt in step 8 is Terraform's documented wording.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `terraform_data.migrated_state` | One record to migrate, so the move is observable | Free |
| Local `terraform.tfstate` | The starting point, created in step 3 | Free |
| S3 object at `labs/lab19/terraform.tfstate` | The migration destination, in lab 17's bucket | Fractions of a cent |

## Before you start

- [ ] [Lab 18 — State keys and locking](lab18-state-keys-locking.md) completed, and **lab 17's S3 bucket still exists** — this lab migrates into the same bucket and does not create one
- [ ] `TF_STATE_BUCKET` exported in this terminal, holding the name you invented in lab 17
- [ ] Terraform 1.11.0 or newer, for generally-available `use_lockfile` (`terraform version`)
- [ ] AWS credentials exported and `aws sts get-caller-identity` working
- [ ] Read [../docs/advanced/state.md](../docs/advanced/state.md)

**If you are starting at this lab, or opened a new terminal since lab 17**, re-export the bucket
name and confirm the bucket exists before you migrate anything into it. A migration that fails
because the destination bucket is missing leaves you restoring from backup for no reason.

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

`NoSuchBucket` means you have not done lab 17 or you deleted the bucket. Run
[lab 17 steps 5 to 9](lab17-s3-backend.md#step-5--choose-a-globally-unique-bucket-name) to create
and version it, then return here. This lab needs only lab 17's bucket, not its state object.

Unlike labs 17 and 18, `main.tf` ships with **no backend block** — you need local state to exist
before there is anything to migrate. Its `required_version` is still `>= 1.11.0`, because the
`backend.hcl.example` you supply in step 7 sets `use_lockfile`, generally available only from
Terraform 1.11.

## Steps

### Step 1 — Confirm you are starting local

```bash
cd terraform/labs/lab19-state-migration
grep -n 'backend' main.tf
```

**Expected output**

```text
2:  # Higher than the track's >= 1.5.0 floor: backend.hcl.example sets use_lockfile,
6:  # Step 6 of the lab manual has you add the S3 backend block here:
7:  #   backend "s3" {}
```

All three matches are comments — line 2 only mentions `backend.hcl.example`. With no active
`backend` block, Terraform defaults to the `local` backend.

### Step 2 — Initialize the local backend

```bash
terraform init
```

**Expected output**

```text
Initializing the backend...
Initializing provider plugins...
- terraform.io/builtin/terraform is built in to Terraform

Terraform has been successfully initialized!
```

Note `Initializing the backend...` with no backend named — that is the `local` default.

### Step 3 — Apply locally to create the state you will move

```bash
terraform apply -auto-approve
ls terraform.tfstate
```

**Expected output**

```text
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

migration_instruction = "migrate with terraform init -migrate-state"
terraform.tfstate
```

That local `terraform.tfstate` is the file the rest of the lab moves.

### Step 4 — Record what state contains

You will compare this list against the post-migration list. If the two differ, the migration
lost something.

```bash
terraform state list
```

**Expected output**

```text
terraform_data.migrated_state
```

### Step 5 — Back the state up before changing anything

Do this before every real migration. The backup is your only way back if the copy goes wrong.

```bash
cp terraform.tfstate terraform.tfstate.pre-migration
ls -1 terraform.tfstate*
```

**Expected output**

```text
terraform.tfstate
terraform.tfstate.pre-migration
```

### Step 6 — Add the backend block

Edit `main.tf` and uncomment the backend line so the `terraform` block reads:

```hcl
terraform {
  required_version = ">= 1.11.0"
  backend "s3" {}
}
```

Leave `required_version` at `>= 1.11.0`. Lowering it lets a learner on 1.9 pass this check and then
fail in step 8 on `use_lockfile`.

### Step 7 — Fill in the destination

```bash
cp backend.hcl.example backend.hcl
# Edit backend.hcl: set bucket to your $TF_STATE_BUCKET name from lab 17. Leave key as shipped.
cat backend.hcl
```

**Expected output** *(bucket will differ — it is your lab 17 name)*

```text
bucket       = "tfstate-yourname-4821"
key          = "labs/lab19/terraform.tfstate"
region       = "us-east-1"
encrypt      = true
use_lockfile = true
```

### Step 8 — Migrate

`-migrate-state` tells Terraform you intend to move the existing state rather than start fresh.
It still asks for confirmation; answer `yes`.

```bash
terraform init -migrate-state -backend-config=backend.hcl
```

**Expected output** *(yours will differ)*

```text
Do you want to copy existing state to the new backend?
  Pre-existing state was found while migrating the previous "local" backend to the
  newly configured "s3" backend. No existing state was found in the newly
  configured "s3" backend. Do you want to copy this state to the new "s3" backend?

  Enter a value: yes

Successfully configured the backend "s3"! Terraform will automatically
use this backend unless the backend configuration changes.
```

In an automated pipeline, add `-force-copy` to answer `yes` without prompting.

### Step 9 — Prove nothing changed

This is the acceptance test for the whole lab. Anything other than no changes means stop and
investigate before applying.

```bash
terraform plan
```

**Expected output** *(yours will differ)*

```text
terraform_data.migrated_state: Refreshing state... [id=c116e480-64e8-1830-cfa7-55dd50911820]

No changes. Your infrastructure matches the configuration.

Terraform has compared your real infrastructure against your configuration
and found no differences, so no changes are needed.
Releasing state lock. This may take a few moments...
```

`Releasing state lock` confirms the plan ran against S3, not a local file.

### Step 10 — Confirm the same resources are in the new state

Compare this against step 4. The addresses must be identical.

```bash
terraform state list
```

**Expected output**

```text
terraform_data.migrated_state
```

### Step 11 — Confirm the object exists in S3

```bash
aws s3 ls "s3://$TF_STATE_BUCKET/labs/lab19/"
```

**Expected output** *(timestamp and size will differ)*

```text
2026-08-29 12:04:11       1204 terraform.tfstate
```

### Step 12 — Note what Terraform left behind locally

Terraform writes a local backup of the pre-migration file automatically, in addition to the copy
you made in step 5.

```bash
ls -1 terraform.tfstate*
```

**Expected output**

```text
terraform.tfstate.backup
terraform.tfstate.pre-migration
```

The live `terraform.tfstate` is gone because state now lives in S3.

## Done when

- [ ] A local `terraform.tfstate` existed before you added the backend block
- [ ] `terraform.tfstate.pre-migration` backup exists
- [ ] `init -migrate-state` reported the backend configured successfully
- [ ] `terraform plan` reported **No changes**
- [ ] `terraform state list` after migration matched the list from step 4
- [ ] The state object exists under `labs/lab19/` in lab 17's bucket

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| Plan wants to create every resource | State was not copied; the remote key is empty | Restore `terraform.tfstate.pre-migration`, remove `.terraform/`, and rerun step 8 answering `yes` |
| `Backend initialization required` | Backend block added but `init` not rerun | Rerun step 8 |
| Terraform never offers to copy | No local state exists | Complete step 3 first |
| `Error acquiring the state lock` | Another operation holds the key | Wait, or `terraform force-unlock <ID>` once you confirm nothing is running |
| `AccessDenied` writing the new key | Policy does not cover this prefix | A policy boundary, not a config error — request access to `labs/*` |
| `Error inspecting states in the "s3" backend` | Wrong bucket or region in `backend.hcl` | Verify both with `aws s3 ls "s3://$TF_STATE_BUCKET"` |
| `NoSuchBucket` at step 8 | Lab 17's bucket was deleted, or `bucket` is still the example placeholder | Recreate it with [lab 17 steps 5 to 9](lab17-s3-backend.md#step-5--choose-a-globally-unique-bucket-name). Your local state and its backup are untouched; rerun step 8 |
| `BucketNotEmpty` at cleanup | Only the current object versions were removed | Run both `delete-objects` calls in the Cleanup section before `delete-bucket` |
| Prompt appears again on a later `init` | `backend.hcl` changed after migration | Use `terraform init -reconfigure` when only re-pointing, not re-copying |
| State list is shorter after migration | A partial copy, or the wrong key | Restore the backup and repeat step 8 |

## Cleanup

This is the end of the S3 backend sequence, so the shared bucket is deleted here. Labs 17 and 18
deferred it to this point. [Lab 20](lab20-remote-state-consumer.md) reads local state files, not
this bucket, so nothing later needs it.

First destroy this lab's resource and remove the local artefacts.

```bash
terraform destroy -auto-approve
rm -f backend.hcl terraform.tfstate.pre-migration
rm -rf .terraform
```

**A versioned bucket cannot be deleted until every object version is gone.** Versioning is what
made state history recoverable, and the price is that `aws s3 rm --recursive` is not enough: it
deletes the *current* version of each object by writing a delete marker, leaving both the old
versions and the markers behind. `delete-bucket` then refuses:

```text
An error occurred (BucketNotEmpty) when calling the DeleteBucket operation: The bucket you tried
to delete is not empty. You must delete all versions in the bucket.
```

Delete the versions and the delete markers explicitly, then the bucket. Run all four commands in
order, in the same terminal where `TF_STATE_BUCKET` is exported.

```bash
aws s3 rm "s3://$TF_STATE_BUCKET" --recursive

aws s3api delete-objects --bucket "$TF_STATE_BUCKET" --delete "$(
  aws s3api list-object-versions --bucket "$TF_STATE_BUCKET" --output json \
    --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}')"

aws s3api delete-objects --bucket "$TF_STATE_BUCKET" --delete "$(
  aws s3api list-object-versions --bucket "$TF_STATE_BUCKET" --output json \
    --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}')"

aws s3api delete-bucket --bucket "$TF_STATE_BUCKET"
```

**Expected output** *(keys and version ids will differ; delete-bucket prints nothing)*

```text
delete: s3://tfstate-yourname-4821/labs/lab19/terraform.tfstate
{
    "Deleted": [
        {
            "Key": "labs/lab17/terraform.tfstate",
            "VersionId": "6GGowVTuN3SXwuxPzVXBbiEvVvxP_CwN"
        },
        {
            "Key": "labs/lab19/terraform.tfstate",
            "VersionId": "9HAkQRsuDD7IbZcORcIhqwAnuA1_CDZG"
        }
    ]
}
{
    "Deleted": [
        {
            "Key": "labs/lab19/terraform.tfstate",
            "VersionId": "NmchHrPXvaXgmCdoYNYxe7e9G3k47TgZ",
            "DeleteMarker": true,
            "DeleteMarkerVersionId": "NmchHrPXvaXgmCdoYNYxe7e9G3k47TgZ"
        }
    ]
}
```

Each `delete-objects` call handles up to 1000 entries per request. Three labs of state produces far
fewer, but on a long-lived bucket rerun both calls until they report nothing left. When a category
is already empty, the query returns no list and the CLI rejects the call locally:

```text
An error occurred (ParamValidation): Parameter validation failed:
Invalid type for parameter Delete.Objects, value: None, type: <class 'NoneType'>
```

That is the "nothing to delete" signal — continue to `delete-bucket`.

Confirm the bucket is gone.

```bash
aws s3 ls "s3://$TF_STATE_BUCKET"
```

**Expected output**

```text
An error occurred (NoSuchBucket) when calling the ListObjectsV2 operation: The specified bucket
does not exist
```

The error is the success condition. Finally, drop the variable.

```bash
unset TF_STATE_BUCKET
```

## Next steps

- Deep dive: [../docs/advanced/state.md](../docs/advanced/state.md)
- Visual: [../html/advanced.html](../html/advanced.html)
- Continue to [Lab 20 — Remote state consumer](lab20-remote-state-consumer.md)
