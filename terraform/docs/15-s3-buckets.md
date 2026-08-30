# S3 Buckets as Managed Resources

Backs lab 23. Covers globally unique bucket names and the random-suffix idiom, the AWS provider 5.x
split of one logical bucket into six separate resources, why that split turns a settings change into
`1 to change` instead of a bucket rewrite, and what `force_destroy` does and does not protect you
from.

## Two different relationships with S3

By lab23 you have used S3 four times and never like this. In labs 17 to 19 and 22, S3 was
**infrastructure Terraform uses**: the bucket held the state file, and you created it with
`aws s3api create-bucket`. That was not laziness. Terraform cannot manage the bucket its own state
lives in — creating the bucket would need a working backend, and the backend needs the bucket to
already exist. The chicken-and-egg problem is why a backend bucket is always created out-of-band; see
[`13-remote-state.md`](13-remote-state.md).

Lab23 is the other case: S3 as **infrastructure Terraform manages**. The bucket is an ordinary
resource in state, created, modified and destroyed by `apply` and `destroy` like an EC2 instance.
Nothing about it is special; it just happens to be the same service. Lab23's own state stays local,
so there is no backend and no bootstrap problem.

**Visual summary:** [`../html/concepts.html`](../html/concepts.html)

## Bucket names are globally unique

**S3 bucket names are unique across every AWS account on Earth**, not per account and not per region.
Every short, obvious name was claimed years ago, so a hardcoded name in a shared manual fails for
everyone who reads it. Worse, the failure arrives at apply rather than plan, because only AWS knows
whether a name is free:

```text
Error: creating S3 Bucket (images): operation error S3: CreateBucket, https response error
StatusCode: 409, RequestID: AH7TCMMBZYRA61DH, BucketAlreadyExists:
```

`BucketAlreadyExists` means another AWS account holds the name. `BucketAlreadyOwnedByYou` is the
sibling error and means *you* already created it — usually a re-run after a partial apply.

Lab23 solves this with a random suffix from the `random` provider:

```hcl
resource "random_pet" "suffix" {
  length    = 2
  separator = "-"
}

locals {
  bucket_name = "${var.bucket_prefix}-${random_pet.suffix.id}"
}
```

That yields something like `tf-lab23-charmed-stud`. The key property is that `random_pet` generates
its words **once, at create time, and stores them in state**, so the name is stable across later
plans and applies — it does not churn on every run, which would replace the bucket each time.

Three idioms solve the same problem and are worth recognising:

| Idiom | Where the suffix comes from | Looks like |
|---|---|---|
| `random_pet` | Two dictionary words, from the random provider | `tf-lab23-charmed-stud` |
| `random_id` | Hex bytes, from the random provider | `tf-lab24-39a8b4ba-logs` (lab24 uses this) |
| `bucket_prefix` on `aws_s3_bucket` | AWS appends a suffix itself; you never set `bucket` | `tf-lab23-20260830...` |

Lab23 uses `random_pet` because the resulting name is readable in the console. Names are 3 to 63
characters, lowercase letters, digits, hyphens and dots only — uppercase or an underscore in
`bucket_prefix` produces `InvalidBucketName`.

## One bucket, six resources

Lab23's `main.tf` declares six resources for what the console displays as a single bucket:

```text
resource "aws_s3_bucket" "lab" {
resource "aws_s3_bucket_versioning" "lab" {
resource "aws_s3_bucket_server_side_encryption_configuration" "lab" {
resource "aws_s3_bucket_public_access_block" "lab" {
resource "aws_s3_bucket_ownership_controls" "lab" {
resource "aws_s3_object" "hello" {
```

| Resource | What it sets |
|---|---|
| `aws_s3_bucket` | The bucket itself: name, `force_destroy`, tags |
| `aws_s3_bucket_versioning` | `Enabled` or `Suspended`; keeps prior copies of every object |
| `aws_s3_bucket_server_side_encryption_configuration` | Default encryption at rest, `AES256` here |
| `aws_s3_bucket_public_access_block` | All four public-access paths blocked |
| `aws_s3_bucket_ownership_controls` | `BucketOwnerEnforced` — ACLs disabled, the owner owns every object |
| `aws_s3_object` | One object, so the bucket is not empty |

Each settings resource points at the bucket the same way:

```hcl
resource "aws_s3_bucket_versioning" "lab" {
  bucket = aws_s3_bucket.lab.id

  versioning_configuration {
    status = var.versioning_status
  }
}
```

That reference is also the dependency: Terraform creates the bucket first and, on `destroy`, deletes
the settings and the object before the bucket, entirely because of it.

Add `random_pet.suffix` and lab23's plan is `Plan: 7 to add, 0 to change, 0 to destroy.`, and
`terraform state list` shows seven entries for one bucket. `bucket` and `tags` read
`(known after apply)` in that plan, because both depend on a `random_pet` that does not exist yet.

### The split is recent, and old examples will not work

Until AWS provider 4.x, versioning, encryption and lifecycle rules were **inline blocks** inside
`aws_s3_bucket`:

```hcl
resource "aws_s3_bucket" "old" {
  bucket = "example"

  versioning {
    enabled = true
  }
}
```

Provider 4.9 deprecated those blocks and 5.x removed them. Any tutorial written before 2022 shows the
inline form, and pasting it into a 5.x configuration fails with `Unsupported block type` or
`Blocks of type "versioning" are not expected here`. This track pins `~> 5.0`, so the separate-resource
form is the only one that works here.

### Why the split produces `1 to change`

The payoff is that each setting plans, changes and destroys independently. Suspend versioning on an
existing bucket and the plan touches one resource:

```text
  # aws_s3_bucket_versioning.lab will be updated in-place
  ~ resource "aws_s3_bucket_versioning" "lab" {
        id                    = "tf-lab23-charmed-stud"

      ~ versioning_configuration {
          ~ status     = "Enabled" -> "Suspended"
        }
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```

`~` is update in place: the resource keeps its identity and one attribute is rewritten. The bucket and
its other four settings are not mentioned, because nothing about them changed — `1 to change`, not a
destroy-and-create of the bucket. Under the pre-4.x inline syntax the same edit rewrote the
`aws_s3_bucket` resource itself, which put the whole bucket in the diff for a one-line change.

## force_destroy

S3 refuses to delete a bucket that still holds objects. `force_destroy = true` tells the provider to
delete every object — **including versions and objects Terraform never created** — before deleting the
bucket. Without it, one stray file left by anything other than this configuration makes `destroy`
fail:

```text
Error: deleting S3 Bucket (tf-lab23-primary-kid): operation error S3: DeleteBucket, https response
error StatusCode: 409, api error BucketNotEmpty: The bucket you tried to delete is not empty. You
must delete all versions in the bucket.
```

Two properties of this argument are easy to get wrong.

**It is read from state, not from the destroy command.** `force_destroy` is an argument on the bucket
resource, and its value is recorded in state at apply time. Passing
`terraform destroy -var force_destroy=false` does not retroactively protect a bucket already recorded
with `force_destroy = true`; changing the protection is an `apply` you run first, and only then does a
later destroy behave differently. Treat it as a property of the bucket, not a flag on a command.

**It only matters for objects Terraform does not manage.** `aws_s3_object.hello` is a managed
resource, so `destroy` deletes it as an ordinary dependency of the bucket, `force_destroy` or not.
What the argument covers is everything else: objects uploaded by an application, by a colleague, by a
log delivery configuration, and — on a versioned bucket — every noncurrent version and delete marker.
That is precisely the data nobody reviewed before the destroy ran.

Lab23 defaults it to `true` so teardown of a throwaway bucket is one command. In production the same
argument turns a `terraform destroy` typo, or a rename that forces replacement, into irreversible data
loss with no prompt beyond the ordinary one. Real buckets set `force_destroy = false` and are emptied
deliberately.

## Verify against the API, not against Terraform

Terraform reporting success is not the same as AWS agreeing, and encryption is the setting most often
assumed rather than checked. Lab23 asks S3 directly:

```bash
BUCKET=$(terraform output -raw bucket_name)
aws s3api get-bucket-versioning --bucket "$BUCKET"
aws s3api get-public-access-block --bucket "$BUCKET"
aws s3api get-bucket-encryption --bucket "$BUCKET" \
  --query 'ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault'
```

All four values in `PublicAccessBlockConfiguration` must be `true`, and the encryption query must
return `{"SSEAlgorithm": "AES256"}`. On a training account an `AccessDenied` here is a policy
boundary rather than a configuration error.

After `destroy`, the success condition is a failure:

```text
aws: [ERROR]: An error occurred (404) when calling the HeadBucket operation: Not Found
```

Note what a 404 also means: the *name* is immediately free for anyone in the world to claim. Deleting
a bucket does not reserve its name for you.

One thing you do not have to get right here, and did have to in lab22: there is no
`LocationConstraint` to pass. The bucket lands in `us-east-2` because the provider block sets the
region.

## Command reference

```bash
cd terraform/labs/lab23-s3-bucket
terraform init
terraform plan                                          # 7 to add
terraform apply
terraform state list                                    # seven entries for one bucket
BUCKET=$(terraform output -raw bucket_name)
aws s3api get-bucket-versioning --bucket "$BUCKET"
terraform plan -var versioning_status=Suspended         # 0 to add, 1 to change, 0 to destroy
terraform apply -auto-approve -var versioning_status=Suspended
terraform destroy                                       # 7 destroyed
aws s3api head-bucket --bucket "$BUCKET"                # 404 is success
```

## Where next

- Many buckets from one resource block, and why the addressing scheme matters:
  [`16-count-foreach.md`](16-count-foreach.md)
- The other relationship with S3 — the bucket that holds state:
  [`13-remote-state.md`](13-remote-state.md)
- The plan symbols this lab exercises, `+`, `~` and `-`: [`03-workflow.md`](03-workflow.md)

## Hands-On Labs

| Lab | Description |
|---|---|
| [Lab 23: S3 bucket as a Terraform resource](../labmanuals/lab23-s3-bucket.md) | Bucket, versioning, encryption, public access block, ownership controls and an object; an in-place settings change; `force_destroy` |
