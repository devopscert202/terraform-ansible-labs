# Lab 24 — count and for_each on real buckets

| | |
|---|---|
| **Goal** | Build six S3 buckets, three with `count` and three with `for_each`, then delete one item from each input and watch the two meta-arguments produce completely different plans. |
| **Time** | 40–50 minutes |
| **Tier** | Advanced |
| **Files** | `../labs/lab24-count-foreach-buckets/` |

## Overview

[Lab 11](lab11-collections.md) introduced `count` and `for_each` on `terraform_data`, a
placeholder that creates nothing. The plans there were real, but the consequences were imaginary.
This lab runs the same comparison against real AWS resources, so the plan you read at the end is
the plan you would read on a production account.

One sentence carries the whole lab: **`count` gives you N identical things addressed by position;
`for_each` gives you N differently-configured things addressed by name.** Position is the problem.
A `count` instance has no identity beyond its index, so removing an item from the middle of the
list shifts every later item down a slot, and Terraform reads that shift as "these resources
changed". A `for_each` instance is bound to its key, and a key does not move when its neighbours
disappear.

S3 buckets make this demonstration affordable. They create in seconds, cost nothing to hold empty,
need no VPC, and their names are globally unique — which makes `count.index` and `each.key`
visible in the name of every real object AWS hands back.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `random_id.suffix` | Eight hex characters appended to every bucket name so the lab runs in any account | None |
| `aws_s3_bucket.by_count` | Three buckets from `count` over a `list(string)`, addressed `[0]`–`[2]` | Free to create; empty buckets store nothing |
| `aws_s3_bucket.by_each` | Three buckets from `for_each` over a `map(object(...))`, addressed by key | Free to create; empty buckets store nothing |
| `aws_s3_bucket_versioning.by_each` | Per-bucket versioning, `Enabled` or `Suspended` from each map entry | None |
| Outputs | Bucket names, versioning status and tags per instance, built with `for` expressions | None |

**This lab is essentially free.** No EC2 instance runs, no VPC is created, and every bucket stays
empty. S3 bills for stored bytes, requests and egress; six empty buckets and a few dozen API calls
round to zero. Destroy them anyway at the end — an account cluttered with orphaned buckets is its
own kind of cost.

## Before you start

- [ ] [Lab 23 — S3 bucket as a managed resource](lab23-s3-bucket.md) completed, so
      `aws_s3_bucket` and the provider 5.x split resources such as `aws_s3_bucket_versioning`
      are already familiar
- [ ] [Lab 11 — Collections](lab11-collections.md) completed, for list, set and map
- [ ] Credentials exported in this terminal, as in [Lab 00](lab00-aws-setup-and-init.md)
- [ ] Permission to create and delete S3 buckets in your training account

## Steps

### Step 1 — Confirm your credentials and region

```bash
aws sts get-caller-identity
echo "$AWS_DEFAULT_REGION"
```

**Expected output**

```text
{
    "UserId": "AIDA2EXAMPLEID4NEXAMPLE",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/odl_user_1234567"
}
us-east-2
```

### Step 2 — Initialize the lab

```bash
cd terraform/labs/lab24-count-foreach-buckets
terraform init
```

**Expected output**

```text
- Installing hashicorp/random v3.9.0...
- Installed hashicorp/random v3.9.0 (signed by HashiCorp)
- Installing hashicorp/aws v5.100.0...
- Installed hashicorp/aws v5.100.0 (signed by HashiCorp)

Terraform has been successfully initialized!
```

Two providers this time. `random` supplies the unique name suffix.

### Step 3 — Read the two inputs

```bash
cat variables.tf
```

The two collections that drive this lab are deliberately different shapes:

```text
variable "bucket_names" {
  type        = list(string)
  description = "Ordered list driving the count example. Position in this list is the only identity a count instance has."
  default     = ["logs", "assets", "backups"]
}

variable "buckets" {
  type = map(object({
    versioning = bool
    tags       = map(string)
  }))
  description = "Map driving the for_each example. The key names the instance; the object configures it."
  default = {
    logs    = { versioning = true, tags = { Retention = "30d", Tier = "ops" } }
    assets  = { versioning = false, tags = { Retention = "none", Tier = "web" } }
    backups = { versioning = true, tags = { Retention = "1y", Tier = "data" } }
  }
}
```

The list carries names and nothing else, because that is all `count` can use. The map carries a
key *and* an object of per-instance settings, which is the reason to reach for `for_each`: three
buckets that are genuinely configured differently, from one resource block.

### Step 4 — Read the two resource blocks

```bash
cat main.tf
```

The `count` block builds three buckets that are identical apart from their name and an index tag:

```text
resource "aws_s3_bucket" "by_count" {
  count = length(var.bucket_names)

  bucket        = "${local.prefix}-count-${var.bucket_names[count.index]}"
  force_destroy = true

  tags = merge(local.common_tags, {
    Name  = "${local.prefix}-count-${var.bucket_names[count.index]}"
    Index = tostring(count.index)
  })
}
```

The `for_each` block builds three buckets that differ in tags, and a second resource that gives
each one its own versioning setting:

```text
resource "aws_s3_bucket" "by_each" {
  for_each = var.buckets

  bucket        = "${local.prefix}-${each.key}"
  force_destroy = true

  tags = merge(each.value.tags, local.common_tags, {
    Name = "${local.prefix}-${each.key}"
  })
}

resource "aws_s3_bucket_versioning" "by_each" {
  for_each = var.buckets

  bucket = aws_s3_bucket.by_each[each.key].id

  versioning_configuration {
    status = each.value.versioning ? "Enabled" : "Suspended"
  }
}
```

Three details worth naming. `count.index` is a number; `each.key` and `each.value` are the map key
and the object under it. `aws_s3_bucket.by_each[each.key].id` is how one `for_each` resource
reaches the matching instance of another — the key is the join between them, which is exactly the
kind of reference that positional indexes make fragile. And `force_destroy = true` lets
`terraform destroy` delete a bucket that still holds objects; convenient in a lab, dangerous in
production, where an accidental destroy would take the contents with it.

### Step 5 — Plan

```bash
terraform plan
```

**Expected output**

```text
Plan: 10 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + count_bucket_names     = [
      + (known after apply),
      + (known after apply),
      + (known after apply),
    ]
  + each_bucket_names      = {
      + assets  = (known after apply)
      + backups = (known after apply)
      + logs    = (known after apply)
    }
  + each_bucket_versioning = {
      + assets  = "Suspended"
      + backups = "Enabled"
      + logs    = "Enabled"
    }
```

Ten resources from four blocks: three `count` buckets, three `for_each` buckets, three versioning
configurations, one random id. The bucket names read `(known after apply)` because they contain a
random value that does not exist yet, while the versioning statuses are already known — they come
from the variable, not from AWS.

### Step 6 — Apply

```bash
terraform apply
```

Type `yes` when prompted.

**Expected output**

```text
random_id.suffix: Creation complete after 0s [id=Oai0ug]
aws_s3_bucket.by_each["assets"]: Creating...
aws_s3_bucket.by_count[0]: Creating...
aws_s3_bucket.by_each["assets"]: Creation complete after 7s [id=tf-lab24-39a8b4ba-assets]
aws_s3_bucket.by_count[0]: Creation complete after 7s [id=tf-lab24-39a8b4ba-count-logs]
aws_s3_bucket_versioning.by_each["assets"]: Creation complete after 3s [id=tf-lab24-39a8b4ba-assets]

Apply complete! Resources: 10 added, 0 changed, 0 destroyed.

Outputs:

count_bucket_names = [
  "tf-lab24-39a8b4ba-count-logs",
  "tf-lab24-39a8b4ba-count-assets",
  "tf-lab24-39a8b4ba-count-backups",
]
each_bucket_names = {
  "assets" = "tf-lab24-39a8b4ba-assets"
  "backups" = "tf-lab24-39a8b4ba-backups"
  "logs" = "tf-lab24-39a8b4ba-logs"
}
each_bucket_versioning = {
  "assets" = "Suspended"
  "backups" = "Enabled"
  "logs" = "Enabled"
}
```

Your suffix will differ. Terraform prints each instance by its address as it works, so the
difference between the two addressing schemes is visible before the apply even finishes.

The outputs come from `for` expressions in `outputs.tf`:

```text
value = { for key, bucket in aws_s3_bucket.by_each : key => bucket.bucket }
```

A `for` expression walks a collection and builds a new one. Listing thirty instances by hand in an
output is not possible; this scales to any number.

### Step 7 — Compare the two kinds of address in state

```bash
terraform state list
```

**Expected output**

```text
aws_s3_bucket.by_count[0]
aws_s3_bucket.by_count[1]
aws_s3_bucket.by_count[2]
aws_s3_bucket.by_each["assets"]
aws_s3_bucket.by_each["backups"]
aws_s3_bucket.by_each["logs"]
aws_s3_bucket_versioning.by_each["assets"]
aws_s3_bucket_versioning.by_each["backups"]
aws_s3_bucket_versioning.by_each["logs"]
random_id.suffix
```

`aws_s3_bucket.by_count[0]` is addressed by number, `aws_s3_bucket.by_each["logs"]` by string key.
These addresses are what Terraform stores, what plans refer to, and what you type into
`state show`, `state rm` and `-target`. Everything else in this lab follows from them.

Inspect one keyed instance — quote the address, or your shell will try to interpret the brackets:

```bash
terraform state show 'aws_s3_bucket_versioning.by_each["assets"]'
```

**Expected output**

```text
# aws_s3_bucket_versioning.by_each["assets"]:
resource "aws_s3_bucket_versioning" "by_each" {
    bucket                = "tf-lab24-39a8b4ba-assets"
    expected_bucket_owner = null
    id                    = "tf-lab24-39a8b4ba-assets"

    versioning_configuration {
        mfa_delete = null
        status     = "Suspended"
    }
}
```

### Step 8 — Prove the for_each buckets really are configured differently

Ask AWS, not Terraform. Replace `39a8b4ba` with your own suffix from the outputs above.

```bash
aws s3api get-bucket-versioning --bucket tf-lab24-39a8b4ba-logs
aws s3api get-bucket-versioning --bucket tf-lab24-39a8b4ba-assets
aws s3api get-bucket-versioning --bucket tf-lab24-39a8b4ba-backups
```

**Expected output**

```text
{
    "Status": "Enabled"
}
{
    "Status": "Suspended"
}
{
    "Status": "Enabled"
}
```

Three instances of one resource block, three different states in AWS, driven entirely by
`each.value.versioning`. This is what `for_each` buys you and `count` cannot.

### Step 9 — Prove the tags differ too

```bash
aws s3api get-bucket-tagging --bucket tf-lab24-39a8b4ba-logs
aws s3api get-bucket-tagging --bucket tf-lab24-39a8b4ba-assets
```

**Expected output**

```text
{
    "TagSet": [
        {
            "Key": "Lab",
            "Value": "lab24"
        },
        {
            "Key": "Retention",
            "Value": "30d"
        },
        {
            "Key": "Tier",
            "Value": "ops"
        },
        {
            "Key": "Name",
            "Value": "tf-lab24-39a8b4ba-logs"
        }
    ]
}
{
    "TagSet": [
        {
            "Key": "Lab",
            "Value": "lab24"
        },
        {
            "Key": "Retention",
            "Value": "none"
        },
        {
            "Key": "Tier",
            "Value": "web"
        },
        {
            "Key": "Name",
            "Value": "tf-lab24-39a8b4ba-assets"
        }
    ]
}
```

`merge(each.value.tags, local.common_tags, { Name = ... })` combined the per-instance tags from the
map with the tags every bucket shares. `Retention` and `Tier` differ per bucket; `Lab` does not.

### Step 10 — Look at what count produced instead

```bash
aws s3api get-bucket-tagging --bucket tf-lab24-39a8b4ba-count-logs
aws s3api get-bucket-versioning --bucket tf-lab24-39a8b4ba-count-logs
```

**Expected output**

```text
{
    "TagSet": [
        {
            "Key": "Lab",
            "Value": "lab24"
        },
        {
            "Key": "Index",
            "Value": "0"
        },
        {
            "Key": "Name",
            "Value": "tf-lab24-39a8b4ba-count-logs"
        }
    ]
}
```

`get-bucket-versioning` printed nothing at all, because versioning was never configured on this
bucket. That is the honest picture of `count`: the only thing distinguishing these three buckets is
`Index`, and `Index` is a fact about the list, not about the bucket. To give the `count` buckets
per-instance settings you would have to index a second list by the same number and keep the two
lists aligned by hand — which is precisely the bookkeeping `for_each` removes.

### Step 11 — Remove the middle list item and plan

This is the step the whole lab exists for. Drop `assets` from the list and see what `count` does
about it. Nothing is applied; `plan` only reports.

```bash
terraform plan -var 'bucket_names=["logs","backups"]'
```

**Expected output**

```text
Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  - destroy
-/+ destroy and then create replacement

Terraform will perform the following actions:

  # aws_s3_bucket.by_count[1] must be replaced
-/+ resource "aws_s3_bucket" "by_count" {
      ~ arn                         = "arn:aws:s3:::tf-lab24-39a8b4ba-count-assets" -> (known after apply)
      ~ bucket                      = "tf-lab24-39a8b4ba-count-assets" -> "tf-lab24-39a8b4ba-count-backups" # forces replacement
      ~ id                          = "tf-lab24-39a8b4ba-count-assets" -> (known after apply)
      ~ tags                        = {
            "Index" = "1"
            "Lab"   = "lab24"
          ~ "Name"  = "tf-lab24-39a8b4ba-count-assets" -> "tf-lab24-39a8b4ba-count-backups"
        }
    }

  # aws_s3_bucket.by_count[2] will be destroyed
  # (because index [2] is out of range for count)
  - resource "aws_s3_bucket" "by_count" {
      - arn                         = "arn:aws:s3:::tf-lab24-39a8b4ba-count-backups" -> null
      - bucket                      = "tf-lab24-39a8b4ba-count-backups" -> null
      - id                          = "tf-lab24-39a8b4ba-count-backups" -> null
      - tags                        = {
          - "Index" = "2"
          - "Lab"   = "lab24"
          - "Name"  = "tf-lab24-39a8b4ba-count-backups"
        } -> null
    }

Plan: 1 to add, 0 to change, 2 to destroy.
```

Read what actually happened. You deleted one item and two buckets are affected. Index `[1]` used to
be `assets`; now the list's second element is `backups`, so Terraform proposes to **destroy the
`assets` bucket and recreate it under the `backups` name** — `# forces replacement`, because a
bucket's name cannot be changed after creation. Index `[2]` no longer exists, so the bucket that
held your backups is destroyed outright.

The bucket you asked to remove is `assets`. The bucket that gets deleted and rebuilt is `backups`.
Terraform is not confused; it is doing exactly what positional identity requires. On real
infrastructure this is how one edit to the middle of a list takes down a database, a load balancer,
or in this case a bucket and everything in it.

### Step 12 — Remove the same entry from the map and plan

```bash
terraform plan -var 'buckets={logs={versioning=true,tags={Retention="30d",Tier="ops"}},backups={versioning=true,tags={Retention="1y",Tier="data"}}}'
```

**Expected output**

```text
Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  - destroy

Terraform will perform the following actions:

  # aws_s3_bucket.by_each["assets"] will be destroyed
  # (because key ["assets"] is not in for_each map)
  - resource "aws_s3_bucket" "by_each" {
      - bucket                      = "tf-lab24-39a8b4ba-assets" -> null
      - id                          = "tf-lab24-39a8b4ba-assets" -> null
      - tags                        = {
          - "Lab"       = "lab24"
          - "Name"      = "tf-lab24-39a8b4ba-assets"
          - "Retention" = "none"
          - "Tier"      = "web"
        } -> null
    }

  # aws_s3_bucket_versioning.by_each["assets"] will be destroyed
  # (because key ["assets"] is not in for_each map)
  - resource "aws_s3_bucket_versioning" "by_each" {
      - bucket                = "tf-lab24-39a8b4ba-assets" -> null
      - id                    = "tf-lab24-39a8b4ba-assets" -> null

      - versioning_configuration {
          - status     = "Suspended" -> null
        }
    }

Plan: 0 to add, 0 to change, 2 to destroy.
```

Two resources destroyed, and both of them belong to the key you removed: the `assets` bucket and
the versioning configuration attached to it. `logs` and `backups` are not mentioned anywhere in the
plan, because nothing about them changed. Their keys did not move.

### Step 13 — Put the two summaries side by side

| Edit | Plan | What was disturbed |
|---|---|---|
| Removed `assets` from the list (`count`) | `1 to add, 0 to change, 2 to destroy` | The `assets` bucket **and** the unrelated `backups` bucket |
| Removed `assets` from the map (`for_each`) | `0 to add, 0 to change, 2 to destroy` | Only the `assets` bucket and its own versioning resource |

The operational rule follows directly: **with `count`, deleting one item from the middle of a list
can destroy and recreate infrastructure you never touched.** Use `for_each` over a map or set for
anything with a natural name — an environment, a service, a bucket, a subnet. Keep `count` for the
cases that genuinely are N interchangeable copies, where no instance means anything on its own, or
for the `count = var.enabled ? 1 : 0` on/off idiom.

### Step 14 — Why for_each needs a set or a map

`for_each` refuses a list, because a list has duplicates and an order, and neither can produce
stable unique keys. `toset()` converts one:

```bash
echo 'toset(var.bucket_names)' | terraform console
```

**Expected output**

```text
toset([
  "assets",
  "backups",
  "logs",
])
```

Three values in, three out, sorted rather than in list order — a set has no order of its own. Give
`for_each` a raw list and Terraform stops before it plans anything:

```text
Error: Invalid for_each argument

  on main.tf line 55, in resource "aws_s3_bucket" "by_each":
  55:   for_each = var.bucket_names
    ├────────────────
    │ var.bucket_names is a list of string

The given "for_each" argument value is unsuitable: the "for_each" argument
must be a map, or set of strings, and you have provided a value of type list
of string.
```

With `for_each = toset(var.bucket_names)` the instances are addressed by their own string value:
`aws_s3_bucket.by_each["logs"]`. That is fine when the value *is* the identity. A map is still
better when each instance needs settings of its own, which is why this lab uses one.

### Step 15 — Destroy everything

```bash
terraform destroy
```

Type `yes`.

**Expected output**

```text
aws_s3_bucket_versioning.by_each["logs"]: Destroying... [id=tf-lab24-39a8b4ba-logs]
aws_s3_bucket.by_count[2]: Destroying... [id=tf-lab24-39a8b4ba-count-backups]
aws_s3_bucket.by_count[0]: Destruction complete after 2s
aws_s3_bucket.by_each["logs"]: Destruction complete after 1s
random_id.suffix: Destroying... [id=Oai0ug]
random_id.suffix: Destruction complete after 0s

Destroy complete! Resources: 10 destroyed.
```

### Step 16 — Confirm nothing is left

```bash
aws s3api list-buckets \
  --query 'Buckets[?starts_with(Name, `tf-lab24-`)].Name' --output text
```

**Expected output**

```text

```

Empty. Filtering on the prefix keeps the check to buckets this lab created — never delete a bucket
you cannot account for.

## Done when

- [ ] `apply` reported `10 added` from four resource blocks
- [ ] `state list` showed `[0]`-style addresses for `count` and `["logs"]`-style for `for_each`
- [ ] `get-bucket-versioning` returned `Enabled` for `logs` and `backups`, `Suspended` for `assets`
- [ ] `get-bucket-tagging` showed different `Retention` and `Tier` values per `for_each` bucket
- [ ] The `count` buckets differed only by `Index` and had no versioning at all
- [ ] Shortening the list reported `1 to add, 0 to change, 2 to destroy`, replacing a bucket you did not edit
- [ ] Shortening the map reported `0 to add, 0 to change, 2 to destroy`, touching only the removed key
- [ ] You can say in one sentence why `for_each` is the default choice
- [ ] `list-buckets` returned nothing for the `tf-lab24-` prefix

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `BucketAlreadyExists` | Bucket names are global across every AWS account; the random suffix collided or was removed | Re-run `terraform apply`, or change `name_prefix` |
| `BucketAlreadyOwnedByYou` | A previous run of this lab left buckets behind | `terraform destroy`, or delete them with `aws s3 rb "s3://<name>" --force` |
| `Invalid for_each argument ... you have provided a value of type list of string` | A list was passed to `for_each` | Wrap it: `for_each = toset(var.bucket_names)` |
| `Invalid index` / `must be accessed on specific instances` | A `count` resource referenced without an index | Use `[0]` for one instance or `[*]` for all |
| `each.key is not supported` | `each` used in a `count` block, or `count.index` in a `for_each` block | `count` gets `count.index`; `for_each` gets `each.key` and `each.value` |
| `no matches found: aws_s3_bucket.by_each[...]` | The shell expanded the brackets | Quote the address: `'aws_s3_bucket.by_each["logs"]'` |
| `Invalid value for input variable` on `-var 'buckets=...'` | The object shape does not match | Every entry needs both `versioning` and `tags` |
| `BucketNotEmpty` on destroy | `force_destroy` was set to `false` | Set it back to `true`, or empty the bucket first |
| `AccessDenied` on `get-bucket-tagging` | Training account lacks `s3:GetBucketTagging` | A policy boundary, not a config error; read the tags from `terraform output each_bucket_tags` instead |
| Plan shows `0 to add` | Already applied, or wrong directory | `pwd`, then `terraform state list` |

## Cleanup

```bash
terraform destroy
```

Step 15 already did this. If state is gone but buckets remain, list them by prefix as in Step 16 and
remove the ones you recognise:

```bash
aws s3 rb "s3://tf-lab24-39a8b4ba-logs" --force
```

`--force` deletes the bucket's contents first. Check the name before you run it.

## Next steps

That is the last lab of the track. You began by exporting a key pair and running `terraform init`
against an empty directory; you finished by reading a plan closely enough to see why one deleted
list item would have destroyed a bucket nobody asked you to touch. That habit — read the plan,
believe the plan — is the whole discipline.

- Deep dive: [../docs/16-count-foreach.md](../docs/16-count-foreach.md) for collections and `for` expressions
- Deep dive: [../docs/13-remote-state.md](../docs/13-remote-state.md) for resource addresses and state surgery
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab24-count-foreach-buckets)
- Whole-track catalog: [../html/index.html](../html/index.html)
