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

That claim — "changes nothing in AWS" — is the whole lab, so there has to be something in AWS for it
to be true *of*. This configuration therefore builds a real VPC before you migrate. You record its
`vpc-` ID in step 4, move the state to S3 in step 8, and confirm in steps 9 and 10 that the plan is
clean and the ID is byte-for-byte the same. A migration that "worked" but recreated your network is
the exact failure this test catches, and a placeholder resource cannot catch it.

**A note on the expected output below.** Every block was captured from a real run against
Terraform v1.14.8, AWS provider v5.100.0 and AWS CLI v2. Values unique to your account — bucket
name, VPC id, version ids, sizes, timestamps — are marked *(yours will differ)*, and the `vpc-`
ids shown throughout are from that one run, so yours will be different but must be **consistent
with each other** between steps 4 and 10.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `terraform_data.migrated_state` | One local record to migrate, so the move is observable | Free |
| `aws_vpc.migrated` | A real VPC, `10.19.0.0/16`, that migration must not disturb | Free |
| Local `terraform.tfstate` | The starting point, created in step 3 | Free |
| S3 object at `labs/lab19/terraform.tfstate` | The migration destination, in lab 17's bucket | Fractions of a cent |

Two managed resources. The VPC is free; only the S3 object costs anything, and that is fractions of
a cent.

## Before you start

- [ ] [Lab 18 — State keys and locking](lab18-state-keys-locking.md) completed, and **lab 17's S3 bucket still exists** — this lab migrates into the same bucket and does not create one
- [ ] `TF_STATE_BUCKET` exported in this terminal, holding the name you invented in lab 17
- [ ] Terraform 1.11.0 or newer, for generally-available `use_lockfile` (`terraform version`)
- [ ] AWS credentials exported and `aws sts get-caller-identity` working
- [ ] Room for one more VPC in `us-east-2` — lab 16's two are still in place at this point in the
  track, and the default limit is five per region
- [ ] Read [../docs/13-remote-state.md](../docs/13-remote-state.md)

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
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installed hashicorp/aws v5.100.0 (signed by HashiCorp)

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

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # aws_vpc.migrated will be created
  + resource "aws_vpc" "migrated" {
      + arn                                  = (known after apply)
      + cidr_block                           = "10.19.0.0/16"
      + default_network_acl_id               = (known after apply)
      + default_route_table_id               = (known after apply)
      + default_security_group_id            = (known after apply)
      + dhcp_options_id                      = (known after apply)
      + enable_dns_hostnames                 = (known after apply)
      + enable_dns_support                   = true
      + enable_network_address_usage_metrics = (known after apply)
      + id                                   = (known after apply)
      + instance_tenancy                     = "default"
      + ipv6_association_id                  = (known after apply)
      + ipv6_cidr_block                      = (known after apply)
      + ipv6_cidr_block_network_border_group = (known after apply)
      + main_route_table_id                  = (known after apply)
      + owner_id                             = (known after apply)
      + tags                                 = {
          + "Lab"  = "lab19"
          + "Name" = "lab19-migrated"
        }
      + tags_all                             = {
          + "Lab"  = "lab19"
          + "Name" = "lab19-migrated"
        }
    }

  # terraform_data.migrated_state will be created
  + resource "terraform_data" "migrated_state" {
      + id     = (known after apply)
      + input  = "migrate with terraform init -migrate-state"
      + output = (known after apply)
    }

Plan: 2 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + migration_instruction = (known after apply)
  + vpc_id                = (known after apply)
terraform_data.migrated_state: Creating...
terraform_data.migrated_state: Creation complete after 0s [id=1f12cc0e-3c5f-7121-4466-aa017e3ef847]
aws_vpc.migrated: Creating...
aws_vpc.migrated: Creation complete after 3s [id=vpc-0857c1131a7717d43]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

migration_instruction = "migrate with terraform init -migrate-state"
vpc_id = "vpc-0857c1131a7717d43"
terraform.tfstate
```

`Apply complete! Resources: 2 added, 0 changed, 0 destroyed.` The VPC now exists in `us-east-2`, and
that local `terraform.tfstate` is the file the rest of the lab moves.

### Step 4 — Record what state contains, and the VPC ID it holds

You will compare both of these against their post-migration values. If either differs, the migration
lost or replaced something.

```bash
terraform state list
terraform output -raw vpc_id
```

**Expected output**

```text
aws_vpc.migrated
terraform_data.migrated_state
vpc-0857c1131a7717d43
```

Two addresses — `aws_vpc.migrated` and `terraform_data.migrated_state` — and one `vpc-` ID.
`-raw` prints the ID with no surrounding quotes and no trailing newline, so your shell prompt
follows it on the same line.

**Write that ID down.** It is the acceptance criterion for the migration: the same VPC, still
running, still managed, after its record has moved to a different storage backend.

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

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

Leave `required_providers` alone and leave `required_version` at `>= 1.11.0`. Lowering it lets a learner on 1.9 pass this check and then
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
region       = "us-east-2"
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
Initializing the backend...
Do you want to copy existing state to the new backend?
  Pre-existing state was found while migrating the previous "local" backend to the
  newly configured "s3" backend. No existing state was found in the newly
  configured "s3" backend. Do you want to copy this state to the new "s3"
  backend? Enter "yes" to copy and "no" to start with an empty state.

  Enter a value: yes

Releasing state lock. This may take a few moments...

Successfully configured the backend "s3"! Terraform will automatically
use this backend unless the backend configuration changes.
Initializing provider plugins...
- terraform.io/builtin/terraform is built in to Terraform
- Reusing previous version of hashicorp/aws from the dependency lock file
- Using previously-installed hashicorp/aws v5.100.0

Terraform has been successfully initialized!
```

In an automated pipeline, add `-force-copy` to answer `yes` without prompting.

### Step 9 — Prove nothing changed

This is the acceptance test for the whole lab. Anything other than no changes means stop and
investigate before applying.

```bash
terraform plan
```

**Expected output**

```text
terraform_data.migrated_state: Refreshing state... [id=1f12cc0e-3c5f-7121-4466-aa017e3ef847]
aws_vpc.migrated: Refreshing state... [id=vpc-0857c1131a7717d43]

No changes. Your infrastructure matches the configuration.

Terraform has compared your real infrastructure against your configuration
and found no differences, so no changes are needed.
Releasing state lock. This may take a few moments...
```

Two `Refreshing state...` lines, one per resource, then `No changes. Your infrastructure matches the
configuration.` and finally `Releasing state lock. This may take a few moments...`.

Three separate facts are in that output. `Refreshing state... [id=vpc-...]` for `aws_vpc.migrated`
proves the new backend knows the VPC's real ID. `No changes` proves the record still matches what AWS
holds. `Releasing state lock` proves the plan ran against S3 rather than a local file — the local
backend has no lock to release.

Anything other than `No changes` means stop. In particular, `2 to add` means the copy did not happen
and you are looking at an empty remote state, with your VPC now unmanaged in AWS. Restore
`terraform.tfstate.pre-migration` before doing anything else.

### Step 10 — Confirm the same resources, and the same VPC, are in the new state

Compare both against step 4. The addresses and the ID must be identical.

```bash
terraform state list
terraform output -raw vpc_id
```

**Expected output**

```text
aws_vpc.migrated
terraform_data.migrated_state
vpc-0857c1131a7717d43
```

The same two addresses and the same `vpc-` ID you wrote down in step 4. Nothing was created, nothing
was destroyed, and the VPC never noticed — the only thing that moved was a JSON file.

### Step 11 — Confirm the object exists in S3

```bash
aws s3 ls "s3://$TF_STATE_BUCKET/labs/lab19/"
```

**Expected output** *(timestamp and size will differ)*

```text
2026-08-31 11:44:36       2798 terraform.tfstate
```

### Step 12 — Note what Terraform left behind locally

Terraform writes a local backup of the pre-migration file automatically, in addition to the copy
you made in step 5.

```bash
ls -1 terraform.tfstate*
```

**Expected output**

```text
terraform.tfstate
terraform.tfstate.backup
terraform.tfstate.pre-migration
```

`terraform.tfstate` is still listed, but it is now **zero bytes** — confirm with `ls -l`. The live
state lives in S3; what remains locally is an empty shell. `terraform.tfstate.backup` holds the
pre-migration contents Terraform saved for you, alongside the copy you took yourself in step 5.

## Done when

- [ ] A local `terraform.tfstate` existed before you added the backend block
- [ ] `apply` reported `2 added`, and you wrote down the `vpc_id`
- [ ] `terraform.tfstate.pre-migration` backup exists
- [ ] `init -migrate-state` reported the backend configured successfully
- [ ] `terraform plan` reported **No changes** and ended with `Releasing state lock`
- [ ] `terraform state list` after migration matched the list from step 4
- [ ] `terraform output -raw vpc_id` after migration returned the **same** ID as step 4
- [ ] The state object exists under `labs/lab19/` in lab 17's bucket
- [ ] `destroy` reported `2 destroyed` and `describe-vpcs` returned an empty list

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| Plan wants to create every resource | State was not copied; the remote key is empty | Restore `terraform.tfstate.pre-migration`, remove `.terraform/`, and rerun step 8 answering `yes`. Do **not** apply: your VPC still exists and applying would create a second one |
| `vpc_id` differs after migration | You applied against an empty remote state and built a new VPC | Delete the extra VPC by ID, restore the backup, and repeat step 8 |
| `VpcLimitExceeded` at step 3 | Lab 16's two VPCs plus others fill the region's limit of five | Destroy an earlier lab's VPC, then retry |
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

First destroy this lab's resources — the VPC is real, so this step is not optional — and remove the
local artefacts.

```bash
terraform destroy -auto-approve
aws ec2 describe-vpcs --region us-east-2 \
  --filters 'Name=tag:Lab,Values=lab19' --query 'Vpcs[].VpcId'
rm -f backend.hcl terraform.tfstate.pre-migration
rm -rf .terraform
```

**Expected output**

```text
terraform_data.migrated_state: Refreshing state... [id=1f12cc0e-3c5f-7121-4466-aa017e3ef847]
aws_vpc.migrated: Refreshing state... [id=vpc-0857c1131a7717d43]

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  - destroy

Terraform will perform the following actions:

  # aws_vpc.migrated will be destroyed
  - resource "aws_vpc" "migrated" {
      - arn                                  = "arn:aws:ec2:us-east-2:027488552956:vpc/vpc-0857c1131a7717d43" -> null
      - assign_generated_ipv6_cidr_block     = false -> null
      - cidr_block                           = "10.19.0.0/16" -> null
      - default_network_acl_id               = "acl-0a54deb9855aeac74" -> null
      - default_route_table_id               = "rtb-0988283682436dc9d" -> null
      - default_security_group_id            = "sg-0aa917835d9aac69b" -> null
      - dhcp_options_id                      = "dopt-0b3fb1f3b525c8788" -> null
      - enable_dns_hostnames                 = false -> null
      - enable_dns_support                   = true -> null
      - enable_network_address_usage_metrics = false -> null
      - id                                   = "vpc-0857c1131a7717d43" -> null
      - instance_tenancy                     = "default" -> null
      - ipv6_netmask_length                  = 0 -> null
      - main_route_table_id                  = "rtb-0988283682436dc9d" -> null
      - owner_id                             = "027488552956" -> null
      - tags                                 = {
          - "Lab"  = "lab19"
          - "Name" = "lab19-migrated"
        } -> null
      - tags_all                             = {
          - "Lab"  = "lab19"
          - "Name" = "lab19-migrated"
        } -> null
        # (4 unchanged attributes hidden)
    }

  # terraform_data.migrated_state will be destroyed
  - resource "terraform_data" "migrated_state" {
      - id     = "1f12cc0e-3c5f-7121-4466-aa017e3ef847" -> null
      - input  = "migrate with terraform init -migrate-state" -> null
      - output = "migrate with terraform init -migrate-state" -> null
    }

Plan: 0 to add, 0 to change, 2 to destroy.

Changes to Outputs:
  - migration_instruction = "migrate with terraform init -migrate-state" -> null
  - vpc_id                = "vpc-0857c1131a7717d43" -> null
terraform_data.migrated_state: Destroying... [id=1f12cc0e-3c5f-7121-4466-aa017e3ef847]
terraform_data.migrated_state: Destruction complete after 0s
aws_vpc.migrated: Destroying... [id=vpc-0857c1131a7717d43]
aws_vpc.migrated: Destruction complete after 2s
Releasing state lock. This may take a few moments...

Destroy complete! Resources: 2 destroyed.
[]
```

`Destroy complete! Resources: 2 destroyed.` followed by an empty list from `describe-vpcs`. Destroy
before deleting the bucket: once the state object is gone, Terraform no longer knows the VPC exists
and you would have to find and delete it by hand.

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
            "Key": "labs/lab19/terraform.tfstate",
            "VersionId": "gX7GlNMHzNXkZzMamqgCWcifxBh_6.oa"
        },
        {
            "Key": "labs/lab19/terraform.tfstate.tflock",
            "VersionId": "oPN95rovgRct5SZqXGvULlGZXwBFsbpx"
        },
        {
            "Key": "labs/lab19/terraform.tfstate.tflock",
            "VersionId": "zDhoAauDfIeu_neVAxyKYAV5xRo0nCIo"
        },
        {
            "Key": "labs/lab19/terraform.tfstate",
            "VersionId": "VZ58fIHOnTEa04Q27daVrpLRX8kxnQ85"
        },
        {
            "Key": "labs/lab19/terraform.tfstate.tflock",
            "VersionId": "V_yaD6YcwZ1MV2wIjS.SYXelxR8yh7qe"
        }
    ]
}
{
    "Deleted": [
        {
            "Key": "labs/lab19/terraform.tfstate.tflock",
            "VersionId": "TcdPhxH4jV4oif54jvRUuViN.GGvZLnS",
            "DeleteMarker": true,
            "DeleteMarkerVersionId": "TcdPhxH4jV4oif54jvRUuViN.GGvZLnS"
        },
        {
            "Key": "labs/lab19/terraform.tfstate.tflock",
            "VersionId": "lLWR3E.G1ctxV1j7RhTH2RCR_KFRLAkZ",
            "DeleteMarker": true,
            "DeleteMarkerVersionId": "lLWR3E.G1ctxV1j7RhTH2RCR_KFRLAkZ"
        },
        {
            "Key": "labs/lab19/terraform.tfstate.tflock",
            "VersionId": "R.hod_dVaKQYvjYbFf07cOKPjEY.u.w6",
            "DeleteMarker": true,
            "DeleteMarkerVersionId": "R.hod_dVaKQYvjYbFf07cOKPjEY.u.w6"
        },
        {
            "Key": "labs/lab19/terraform.tfstate",
            "VersionId": "nAICJ0VHh.8PFvG1ZJtcQv4KtQe7p_Iz",
            "DeleteMarker": true,
            "DeleteMarkerVersionId": "nAICJ0VHh.8PFvG1ZJtcQv4KtQe7p_Iz"
        }
    ]
}
```

Note the `.tflock` keys. `use_lockfile = true` writes the state lock as an S3 object beside the
state, so every lock acquired and released during the lab left its own version and delete marker
behind. The capture above is from a run that did only lab 19; if you carried the bucket through
labs 17 and 18 you will see their `labs/lab17/` and `labs/lab18/` keys listed too.

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
aws: [ERROR]: An error occurred (NoSuchBucket) when calling the ListObjectsV2 operation: The specified bucket does not exist
```

Older AWS CLI v2 releases print the same message without the `aws: [ERROR]:` prefix and wrap it
across two lines. Either form is the success condition.

The error is the success condition. Finally, drop the variable.

```bash
unset TF_STATE_BUCKET
```

## Next steps

- Deep dive: [../docs/13-remote-state.md](../docs/13-remote-state.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab19-state-migration)
- Continue to [Lab 20 — Remote state consumer](lab20-remote-state-consumer.md)
