# Lab 23 — S3 bucket as a Terraform resource

| | |
|---|---|
| **Goal** | Create an S3 bucket, its versioning, encryption and access settings as Terraform resources, change one of them in place, then destroy the whole set. |
| **Time** | 30–40 minutes |
| **Tier** | Advanced |
| **Files** | `../labs/lab23-s3-bucket/` |

## Overview

You have already used S3 four times, and never like this. In labs 17 to 19 and 22, S3 was
**infrastructure Terraform uses**: the bucket held the state file, and you built it with the AWS
CLI. That was not laziness. Terraform cannot manage the bucket its own state lives in — creating
the bucket would need a working backend, and the backend needs the bucket to already exist. That
chicken-and-egg problem is why the backend bucket is always created out-of-band.

This lab is the other case: S3 as **infrastructure Terraform manages**. The bucket is an ordinary
resource in state, created, modified and destroyed by `apply` and `destroy` like an EC2 instance.
Nothing about it is special; it just happens to be the same service. State for this lab stays
local, so there is no backend and no bootstrap problem.

The lab is also a closing exercise on the resource lifecycle: you create, then change one setting
and read the `~` in-place update in the plan, then tear everything down and confirm through the
AWS API that it is gone.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `random_pet.suffix` | Two random words appended to the bucket name so it is globally unique | None |
| `aws_s3_bucket.lab` | The bucket itself | Free to create; storage is billed per GB-month |
| `aws_s3_bucket_versioning.lab` | Keeps prior copies of every object | None |
| `aws_s3_bucket_server_side_encryption_configuration.lab` | Encrypts objects at rest with AES256 | None |
| `aws_s3_bucket_public_access_block.lab` | Blocks all four public-access paths | None |
| `aws_s3_bucket_ownership_controls.lab` | Disables ACLs; the bucket owner owns every object | None |
| `aws_s3_object.hello` | One 29-byte text object, so the bucket is not empty | Effectively zero |

**This lab is effectively free.** No EC2 instance runs. S3 charges for storage, requests and
egress; 29 bytes and a few dozen API calls round to nothing at the monthly bill's precision. It is
still not zero forever, which is why the bucket is destroyed at the end.

## Before you start

- [ ] [Lab 22 — EC2 with remote state in S3](lab22-ec2-s3-backend.md) completed
- [ ] Credentials exported in this terminal ([Lab 00](lab00-aws-setup-and-init.md)), `aws sts get-caller-identity` works
- [ ] Terraform 1.5.0 or newer — this lab has no backend and needs no higher floor
- [ ] Permission to call `s3:CreateBucket`, `s3:PutBucket*`, `s3:PutObject` and `s3:DeleteBucket`

## Steps

### Step 1 — Read how the bucket gets a unique name

**S3 bucket names are globally unique across every AWS account on Earth**, not per-account and not
per-region. Every short, obvious name was claimed years ago, so a hardcoded name in a shared
manual fails for everyone who reads it.

```bash
cd terraform/labs/lab23-s3-bucket
grep -A3 'resource "random_pet"' main.tf
```

**Expected output**

```text
resource "random_pet" "suffix" {
  length    = 2
  separator = "-"
}
```

`local.bucket_name` is `"${var.bucket_prefix}-${random_pet.suffix.id}"`, giving something like
`tf-lab23-charmed-stud`. The `random` provider generates the words once, at create time, and stores
them in state, so the name is stable across later plans and applies — it does not churn on every
run. Two other idioms solve the same problem: `bucket_prefix = "tf-lab23-"` on `aws_s3_bucket`,
which makes AWS append the suffix, and `random_id` for hex instead of words. `random_pet` is used
here because the resulting name is readable in the console.

### Step 2 — See what a colliding name costs

This is the failure the random suffix prevents. Terraform plans fine and dies at apply, because
name availability is only known to AWS:

```text
Error: creating S3 Bucket (images): operation error S3: CreateBucket, https response error
StatusCode: 409, RequestID: AH7TCMMBZYRA61DH, BucketAlreadyExists:

  with aws_s3_bucket.collide,
  on main.tf line 7, in resource "aws_s3_bucket" "collide":
   7: resource "aws_s3_bucket" "collide" { bucket = "images" }
```

`BucketAlreadyExists` means another AWS account holds the name. `BucketAlreadyOwnedByYou` is the
sibling error and means *you* already created it — usually a re-run after a partial apply.

### Step 3 — Read the separate settings resources

```bash
grep '^resource' main.tf
```

**Expected output**

```text
resource "random_pet" "suffix" {
resource "aws_s3_bucket" "lab" {
resource "aws_s3_bucket_versioning" "lab" {
resource "aws_s3_bucket_server_side_encryption_configuration" "lab" {
resource "aws_s3_bucket_public_access_block" "lab" {
resource "aws_s3_bucket_ownership_controls" "lab" {
resource "aws_s3_object" "hello" {
```

One logical bucket, seven resource blocks: six AWS resources plus the `random_pet` that names it.
That split is deliberate and recent. Until AWS provider 4.x,
versioning, encryption and lifecycle rules were **inline blocks** inside `aws_s3_bucket`:

```hcl
resource "aws_s3_bucket" "old" {
  bucket = "example"

  versioning {
    enabled = true
  }
}
```

Provider 4.9 deprecated those blocks and 5.x removed them. Any blog post or tutorial written before
2022 shows the inline form, and pasting it into a 5.x module fails with
`Unsupported block type` or `Blocks of type "versioning" are not expected here`. Each setting is now
its own resource that points at the bucket by `bucket = aws_s3_bucket.lab.id`. The upside is that
each setting plans, changes and destroys independently — which is exactly what Step 8 exploits.

### Step 4 — Read the `force_destroy` argument

```bash
grep -A4 'variable "force_destroy"' variables.tf
```

**Expected output**

```text
variable "force_destroy" {
  description = "Allow terraform destroy to delete the bucket even when it still contains objects."
  type        = bool
  default     = true
}
```

S3 refuses to delete a non-empty bucket. `force_destroy = true` tells the provider to delete every
object — **including versions and objects Terraform never created** — before deleting the bucket.
Without it, a stray file left by anything other than this module makes `destroy` fail:

```text
Error: deleting S3 Bucket (tf-lab23-primary-kid): operation error S3: DeleteBucket, https response
error StatusCode: 409, api error BucketNotEmpty: The bucket you tried to delete is not empty. You
must delete all versions in the bucket.
```

The lab defaults it to `true` so teardown is one command on a throwaway bucket. In production this
argument turns a `terraform destroy` typo, or a rename that forces replacement, into irreversible
data loss with no confirmation prompt beyond the ordinary one. Real buckets set
`force_destroy = false` and are emptied deliberately.

### Step 5 — Initialize and preview

```bash
terraform init
terraform plan
```

**Expected output** *(trimmed)*

```text
Terraform will perform the following actions:

  # aws_s3_bucket.lab will be created
  + resource "aws_s3_bucket" "lab" {
      + bucket        = (known after apply)
      + force_destroy = true
      + id            = (known after apply)
      + tags          = (known after apply)
    }

  # aws_s3_bucket_public_access_block.lab will be created
  + resource "aws_s3_bucket_public_access_block" "lab" {
      + block_public_acls       = true
      + block_public_policy     = true
      + ignore_public_acls      = true
      + restrict_public_buckets = true
    }

  # aws_s3_bucket_versioning.lab will be created
  + resource "aws_s3_bucket_versioning" "lab" {
      + versioning_configuration {
          + status = "Enabled"
        }
    }

  # random_pet.suffix will be created
  + resource "random_pet" "suffix" {
      + length    = 2
      + separator = "-"
    }

Plan: 7 to add, 0 to change, 0 to destroy.
```

`bucket` and `tags` read `(known after apply)` because both depend on `random_pet.suffix.id`, which
does not exist yet.

### Step 6 — Create everything

```bash
terraform apply
```

Type `yes`.

**Expected output** *(names will differ — that is the point of the random suffix)*

```text
random_pet.suffix: Creating...
random_pet.suffix: Creation complete after 0s [id=charmed-stud]
aws_s3_bucket.lab: Creating...
aws_s3_bucket.lab: Creation complete after 7s [id=tf-lab23-charmed-stud]
aws_s3_bucket_ownership_controls.lab: Creation complete after 1s [id=tf-lab23-charmed-stud]
aws_s3_object.hello: Creation complete after 2s [id=hello.txt]
aws_s3_bucket_public_access_block.lab: Creation complete after 2s [id=tf-lab23-charmed-stud]
aws_s3_bucket_server_side_encryption_configuration.lab: Creation complete after 2s [id=tf-lab23-charmed-stud]
aws_s3_bucket_versioning.lab: Creation complete after 3s [id=tf-lab23-charmed-stud]

Apply complete! Resources: 7 added, 0 changed, 0 destroyed.

Outputs:

bucket_arn = "arn:aws:s3:::tf-lab23-charmed-stud"
bucket_name = "tf-lab23-charmed-stud"
bucket_region = "us-east-2"
object_uri = "s3://tf-lab23-charmed-stud/hello.txt"
```

The bucket landed in `us-east-2` because the provider block sets the region. Unlike
`aws s3api create-bucket`, there is no `LocationConstraint` flag to get wrong.

### Step 7 — List what one bucket became in state

```bash
terraform state list
```

**Expected output**

```text
aws_s3_bucket.lab
aws_s3_bucket_ownership_controls.lab
aws_s3_bucket_public_access_block.lab
aws_s3_bucket_server_side_encryption_configuration.lab
aws_s3_bucket_versioning.lab
aws_s3_object.hello
random_pet.suffix
```

Seven state entries for what the console shows as one bucket. Each is separately addressable by
`terraform state show`, `taint`, or `-target`.

### Step 8 — Verify the settings against the AWS API

Terraform reporting success is not the same as AWS agreeing. Ask S3 directly.

```bash
BUCKET=$(terraform output -raw bucket_name)
aws s3api get-bucket-versioning --bucket "$BUCKET"
aws s3api get-public-access-block --bucket "$BUCKET"
aws s3 ls "s3://$BUCKET"
```

**Expected output** *(timestamp will differ)*

```text
{
    "Status": "Enabled"
}
{
    "PublicAccessBlockConfiguration": {
        "BlockPublicAcls": true,
        "IgnorePublicAcls": true,
        "BlockPublicPolicy": true,
        "RestrictPublicBuckets": true
    }
}
2026-08-30 17:23:38         29 hello.txt
```

Encryption is worth one extra call, since it is the setting most often assumed rather than checked:

```bash
aws s3api get-bucket-encryption --bucket "$BUCKET" \
  --query 'ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault'
```

**Expected output**

```text
{
    "SSEAlgorithm": "AES256"
}
```

### Step 9 — Change one setting and read the `~` diff

Suspend versioning. `-var` overrides the default for this run only, so nothing on disk changes.

```bash
terraform plan -var versioning_status=Suspended
```

**Expected output** *(trimmed to the changed resource)*

```text
Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  ~ update in-place

Terraform will perform the following actions:

  # aws_s3_bucket_versioning.lab will be updated in-place
  ~ resource "aws_s3_bucket_versioning" "lab" {
        id                    = "tf-lab23-charmed-stud"
        # (2 unchanged attributes hidden)

      ~ versioning_configuration {
          ~ status     = "Enabled" -> "Suspended"
            # (1 unchanged attribute hidden)
        }
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```

`~` is update in-place: the resource keeps its identity and one attribute is rewritten. Because
versioning is its own resource, the bucket and its five other settings are untouched — `1 to
change`, not `1 to destroy, 1 to add`. Under the pre-4.x inline syntax the same edit rewrote the
`aws_s3_bucket` resource itself.

### Step 10 — Apply the change and confirm it took

```bash
terraform apply -auto-approve -var versioning_status=Suspended
aws s3api get-bucket-versioning --bucket "$BUCKET"
```

**Expected output**

```text
aws_s3_bucket_versioning.lab: Modifying... [id=tf-lab23-charmed-stud]
aws_s3_bucket_versioning.lab: Modifications complete after 3s [id=tf-lab23-charmed-stud]

Apply complete! Resources: 0 added, 1 changed, 0 destroyed.
{
    "Status": "Suspended"
}
```

### Step 11 — Destroy the bucket and everything attached to it

```bash
terraform destroy
```

Type `yes`.

**Expected output** *(trimmed)*

```text
Plan: 0 to add, 0 to change, 7 to destroy.

aws_s3_bucket_versioning.lab: Destruction complete after 0s
aws_s3_object.hello: Destruction complete after 1s
aws_s3_bucket_public_access_block.lab: Destruction complete after 1s
aws_s3_bucket_server_side_encryption_configuration.lab: Destruction complete after 1s
aws_s3_bucket_ownership_controls.lab: Destruction complete after 2s
aws_s3_bucket.lab: Destroying... [id=tf-lab23-charmed-stud]
aws_s3_bucket.lab: Destruction complete after 1s
random_pet.suffix: Destruction complete after 0s

Destroy complete! Resources: 7 destroyed.
```

Terraform deletes the settings and the object first, then the bucket. Dependency order is derived
from the `bucket = aws_s3_bucket.lab.id` references and reversed for destroy.

### Step 12 — Confirm the bucket is gone

```bash
aws s3api head-bucket --bucket "$BUCKET"
```

**Expected output**

```text
aws: [ERROR]: An error occurred (404) when calling the HeadBucket operation: Not Found
```

A 404 here is the success condition. Note that the *name* is now free for anyone in the world to
claim — deleting a bucket does not reserve its name for you.

## Done when

- [ ] `terraform plan` showed `7 to add`
- [ ] `bucket_name` ends in two random words you did not type
- [ ] `aws s3api get-bucket-versioning` reported `"Status": "Enabled"`
- [ ] All four `PublicAccessBlockConfiguration` values were `true`
- [ ] `terraform state list` showed seven entries for one bucket
- [ ] The versioning plan showed `~ status = "Enabled" -> "Suspended"` and `1 to change`
- [ ] `terraform destroy` reported `7 destroyed`
- [ ] `aws s3api head-bucket` returned `404 Not Found`
- [ ] You can state why lab 17 created its bucket with the CLI and this lab does not

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `BucketAlreadyExists` | Another account owns the name; you hardcoded `bucket` or reused a prefix that is itself a whole name | Keep the `random_pet` suffix, or change `bucket_prefix` |
| `BucketAlreadyOwnedByYou` | A previous partial apply already created it | `terraform import aws_s3_bucket.lab <name>`, or delete the bucket and re-apply |
| `InvalidBucketName` | `bucket_prefix` has uppercase letters or underscores | Lowercase letters, digits and hyphens only, 3–63 characters total |
| `BucketNotEmpty` on destroy | `force_destroy = false` and something put objects in the bucket | Empty it with `aws s3 rm "s3://$BUCKET" --recursive`, then destroy again |
| `Blocks of type "versioning" are not expected here` | Inline settings copied from a pre-4.x tutorial | Use the separate `aws_s3_bucket_versioning` resource, as this lab does |
| `NoSuchBucket` on an `aws s3api` call | `$BUCKET` is empty in this terminal, or you already destroyed | Re-run `BUCKET=$(terraform output -raw bucket_name)` |
| `AccessDenied` on `get-bucket-encryption` | Training account lacks `s3:GetEncryptionConfiguration` | A policy boundary, not a config error; skip the check |
| Plan shows `0 to add` | Already applied, or wrong directory | `pwd`, then `terraform state list` |
| Destroy leaves the bucket in the console | Console cache | Refresh, then confirm with `aws s3api head-bucket` |

## Cleanup

```bash
terraform destroy
```

Step 11 already did this. If state is gone but the bucket is not, delete it directly — replace the
name with your own, and check it is one you created:

```bash
aws s3 rb "s3://tf-lab23-charmed-stud" --force
```

## Next steps

You now have a resource you can create many of, which is exactly what the last lab needs.

- Deep dive: [../docs/15-s3-buckets.md](../docs/15-s3-buckets.md) and [../docs/17-project-structure.md](../docs/17-project-structure.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab23-s3-bucket)
- Continue to [Lab 24 — count and for_each on real buckets](lab24-count-foreach-buckets.md)
