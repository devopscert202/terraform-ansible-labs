# count Versus for_each on Real Resources

Backs lab 24. Covers the one distinction that decides which meta-argument to use — `count` addresses
by position, `for_each` addresses by key — and what that costs on real infrastructure when an input
changes.

This is the real-AWS sequel to [`09-collections-functions.md`](09-collections-functions.md). Lab11
taught the same contrast on `terraform_data`, a placeholder that creates nothing: the plans were real
but the consequences were imaginary. Lab24 runs the comparison against S3 buckets, so the plan you
read at the end is the plan you would read on a production account. Read lab11's write-up first if
`for_each`, `each.key` or `count.index` is unfamiliar.

**Visual summary:** [`../html/concepts.html`](../html/concepts.html)

## One sentence

**`count` gives you N identical things addressed by position; `for_each` gives you N
differently-configured things addressed by name.**

Position is the problem. A `count` instance has no identity beyond its index, so removing an item from
the middle of the list shifts every later item down a slot, and Terraform reads that shift as "these
resources changed". A `for_each` instance is bound to its key, and a key does not move when its
neighbours disappear.

S3 buckets make the demonstration affordable: they create in seconds, cost nothing to hold empty, need
no VPC, and their globally unique names put `count.index` and `each.key` into the name of every real
object AWS hands back.

## The two inputs are different shapes

```hcl
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

The list carries names and nothing else, because that is all `count` can use. The map carries a key
*and* an object of per-instance settings, which is the reason to reach for `for_each`: three buckets
genuinely configured differently, from one resource block.

## The two resource blocks

```hcl
resource "aws_s3_bucket" "by_count" {
  count = length(var.bucket_names)

  bucket        = "${local.prefix}-count-${var.bucket_names[count.index]}"
  force_destroy = true

  tags = merge(local.common_tags, {
    Name  = "${local.prefix}-count-${var.bucket_names[count.index]}"
    Index = tostring(count.index)
  })
}

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

| Element | `count` | `for_each` |
|---|---|---|
| Takes | A number | A map, or a set of strings |
| Iteration variable | `count.index` — 0, 1, 2… | `each.key` and `each.value` |
| Address | `aws_s3_bucket.by_count[0]` | `aws_s3_bucket.by_each["logs"]` |
| Address stability | **Tied to position** | **Tied to key** |

`aws_s3_bucket.by_each[each.key].id` is how one `for_each` resource reaches the matching instance of
another. The key is the join between them — exactly the kind of reference a positional index makes
fragile, since the two resources would have to be kept aligned by hand. `local.prefix` includes a
`random_id` suffix for the same reason lab23 uses `random_pet`: bucket names are global, so the lab has
to be runnable by everyone at once.

Those three blocks and the `random_id` produce ten resources in total, and their addresses are the
whole lesson:

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

These addresses are what Terraform stores, what plans refer to, and what you type into `state show`,
`state rm` and `-target`. Quote them in a shell, or it will try to interpret the brackets.

## What count cannot do

Ask AWS what the `for_each` buckets look like and each one differs: `get-bucket-versioning` returns
`Enabled` for `logs` and `backups` and `Suspended` for `assets`, and `get-bucket-tagging` returns a
different `Retention` and `Tier` per bucket, all driven by `each.value`.

Ask the same of a `count` bucket and `get-bucket-versioning` prints nothing at all — versioning was
never configured on it. The only thing distinguishing the three `count` buckets is the `Index` tag,
and `Index` is a fact about the list, not about the bucket. Giving the `count` buckets per-instance
settings would mean indexing a second list by the same number and keeping the two lists aligned by
hand, which is precisely the bookkeeping `for_each` removes.

## The plans that matter

Both edits below remove the same logical thing — `assets` — and nothing is applied; `plan` only
reports.

### Removing the middle item from the list

```bash
terraform plan -var 'bucket_names=["logs","backups"]'
```

```text
  # aws_s3_bucket.by_count[1] must be replaced
-/+ resource "aws_s3_bucket" "by_count" {
      ~ bucket = "tf-lab24-39a8b4ba-count-assets" -> "tf-lab24-39a8b4ba-count-backups" # forces replacement
    }

  # aws_s3_bucket.by_count[2] will be destroyed
  # (because index [2] is out of range for count)
  - resource "aws_s3_bucket" "by_count" {
      - bucket = "tf-lab24-39a8b4ba-count-backups" -> null
    }

Plan: 1 to add, 0 to change, 2 to destroy.
```

Read what actually happened. You deleted one item and two buckets are affected. Index `[1]` used to be
`assets`; now the list's second element is `backups`, so Terraform proposes to destroy the `assets`
bucket and recreate it under the `backups` name — `# forces replacement`, because **a bucket's name
cannot be changed after creation**. Index `[2]` no longer exists, so the bucket that held your backups
is destroyed outright.

The bucket you asked to remove is `assets`. The bucket that gets deleted and rebuilt is `backups`.
Terraform is not confused; it is doing exactly what positional identity requires.

### Removing the same key from the map

```bash
terraform plan -var 'buckets={logs={versioning=true,tags={Retention="30d",Tier="ops"}},backups={versioning=true,tags={Retention="1y",Tier="data"}}}'
```

```text
  # aws_s3_bucket.by_each["assets"] will be destroyed
  # (because key ["assets"] is not in for_each map)

  # aws_s3_bucket_versioning.by_each["assets"] will be destroyed
  # (because key ["assets"] is not in for_each map)

Plan: 0 to add, 0 to change, 2 to destroy.
```

Two resources destroyed, and both belong to the key you removed: the `assets` bucket and the
versioning configuration attached to it. `logs` and `backups` are not mentioned anywhere in the plan,
because nothing about them changed. Their keys did not move.

### Side by side

| Edit | Plan | What was disturbed |
|---|---|---|
| Removed `assets` from the list (`count`) | `1 to add, 0 to change, 2 to destroy` | The `assets` bucket **and** the unrelated `backups` bucket |
| Removed `assets` from the map (`for_each`) | `0 to add, 0 to change, 2 to destroy` | Only the `assets` bucket and its own versioning resource |

The operational rule follows directly: **with `count`, deleting one item from the middle of a list can
destroy and recreate infrastructure you never touched.** Use `for_each` over a map or set for anything
with a natural name — an environment, a service, a bucket, a subnet. Keep `count` for cases that
genuinely are N interchangeable copies where no instance means anything on its own, or for the
`count = var.enabled ? 1 : 0` on/off idiom.

## for_each needs a set or a map

`for_each` refuses a list, because a list has duplicates and an order, and neither can produce stable
unique keys. Hand it one and Terraform stops before it plans anything:

```text
Error: Invalid for_each argument

  55:   for_each = var.bucket_names
    ├────────────────
    │ var.bucket_names is a list of string

The given "for_each" argument value is unsuitable: the "for_each" argument
must be a map, or set of strings, and you have provided a value of type list
of string.
```

`toset()` converts one, and the instances are then addressed by their own string value —
`aws_s3_bucket.by_each["logs"]`. Three values in, three out, sorted rather than in list order, since a
set has no order of its own. That is fine when the value *is* the identity. A map is still better when
each instance needs settings of its own, which is why lab24 uses one.

## Reading many instances in an output

Listing thirty instances by hand in an output is not possible, so both forms have a shorthand:

```hcl
output "count_bucket_names" {
  value = aws_s3_bucket.by_count[*].bucket
}

output "each_bucket_names" {
  value = { for key, bucket in aws_s3_bucket.by_each : key => bucket.bucket }
}
```

`[*]` is the splat operator and is valid only on `count` instances. `for_each` instances are a map, so
a `for` expression keyed by `each.key` is the readable form — and it stays readable at any instance
count. `for` expressions are covered in [`09-collections-functions.md`](09-collections-functions.md).

## Command reference

```bash
cd terraform/labs/lab24-count-foreach-buckets
terraform init
terraform plan                                    # 10 to add
terraform apply
terraform state list                              # [0] addresses vs ["logs"] addresses
terraform state show 'aws_s3_bucket_versioning.by_each["assets"]'
terraform plan -var 'bucket_names=["logs","backups"]'   # 1 to add, 0 to change, 2 to destroy
terraform destroy
aws s3api list-buckets \
  --query 'Buckets[?starts_with(Name, `tf-lab24-`)].Name' --output text
```

## Where next

- The same contrast on a free placeholder resource, plus `for` expressions and the function library:
  [`09-collections-functions.md`](09-collections-functions.md)
- Generating repeated nested blocks rather than repeated resources:
  [`14-dynamic-blocks.md`](14-dynamic-blocks.md)
- The single bucket this lab multiplies: [`15-s3-buckets.md`](15-s3-buckets.md)

## Hands-On Labs

| Lab | Description |
|---|---|
| [Lab 11: Collections](../labmanuals/lab11-collections.md) | The same contrast on `terraform_data`, at no cost |
| [Lab 24: count and for_each on real buckets](../labmanuals/lab24-count-foreach-buckets.md) | Six real buckets, two addressing schemes, and the two plans that show why the choice matters |
