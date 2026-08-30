# Lab 11 — Collections

| | |
|---|---|
| **Goal** | Tell list, set, and map apart, then create many copies of a resource with `count` and with `for_each` and prove why their addressing schemes behave differently when the input changes. |
| **Time** | 40–50 minutes |
| **Tier** | Intermediate |
| **Files** | `terraform/labs/lab11-collections/` |

## Overview

So far your variables held one value each. A **collection type** holds several. HCL has three that
matter: a **list** is ordered and allows duplicates, addressed by position (`0`, `1`, `2`); a **set**
is unordered and silently drops duplicates; a **map** is a set of key/value pairs addressed by a
string key.

Collections earn their keep with the two **meta-arguments** that create many copies of one resource
block. `count` takes a number and makes copies addressed by index. `for_each` takes a set or a map
and makes copies addressed by key. The second half of this lab is the payoff: you will remove one
item from a list and one item from a map, and watch Terraform propose two very different plans. That
contrast is the reason experienced practitioners reach for `for_each` by default.

The resources here are `terraform_data`, a built-in placeholder that creates nothing in any cloud,
so this lab is free and needs no AWS credentials.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `var.tag_names` | A `list(string)` with a deliberate duplicate | Free |
| `var.availability_zones` | A `set(string)` with a duplicate that gets dropped | Free |
| `var.subnets` | A `map(object(...))` of subnet definitions | Free |
| `terraform_data.by_count` | Three copies made with `count`, addressed `[0]`–`[2]` | Free |
| `terraform_data.by_each` | Two copies made with `for_each`, addressed by map key | Free |

## Before you start

- [ ] Lab 10 completed ([lab10-capstone-vpc-ec2.md](lab10-capstone-vpc-ec2.md))
- [ ] You have seen `map(string)` used for tags in Lab 06
- [ ] You have used `terraform console` — if not, Lab 11 covers it; Step 2 here is a first taste
- [ ] Working directory: `../labs/lab11-collections/` (no AWS credentials needed)

## Steps

### Step 1 — Read the three collection types

```bash
cd terraform/labs/lab11-collections
cat variables.tf
```

**Expected output**

```text
variable "tag_names" {
  type        = list(string)
  description = "A list: ordered, duplicates allowed, indexed by number."
  default     = ["web", "api", "web"]
}

variable "availability_zones" {
  type        = set(string)
  description = "A set: unordered, duplicates removed automatically."
  default     = ["us-east-2a", "us-east-2b", "us-east-2a"]
}

variable "subnets" {
  type        = map(object({ cidr = string, az = string }))
  description = "A map: each value is looked up by a string key instead of a number."
  default = {
    app_a = { cidr = "10.0.1.0/24", az = "us-east-2a" }
    app_b = { cidr = "10.0.2.0/24", az = "us-east-2b" }
  }
}
```

`tag_names` contains `web` twice. `availability_zones` also lists a value twice. `subnets` is a map
whose values are objects, each with two named attributes of declared types.

### Step 2 — Explore the types in the console

```bash
terraform init
terraform console
```

At the `>` prompt:

```text
toset(["web","api","web"])
keys(var.subnets)
var.subnets["app_a"].cidr
```

**Expected output**

```text
toset([
  "api",
  "web",
])
tolist([
  "app_a",
  "app_b",
])
"10.0.1.0/24"
```

Three values went into `toset()` and two came out. `keys()` returns a map's keys, and a map value is
reached with `["key"]` followed by the attribute name. Type `exit` to return to your shell.

### Step 3 — Read the `count` block

```bash
grep -B 2 -A 2 'count = ' main.tf
```

**Expected output**

```text
# count makes copies addressed by number: terraform_data.by_count[0], [1], [2].
resource "terraform_data" "by_count" {
  count = length(var.tag_names)
  input = var.tag_names[count.index]
}
```

`count` needs a number, so `length()` converts the list into one. Inside the block, `count.index`
holds the current copy's position, starting at `0`.

### Step 4 — Read the `for_each` block

```bash
grep -B 2 -A 6 'for_each = ' main.tf
```

**Expected output**

```text
# for_each makes copies addressed by key: terraform_data.by_each["app_a"].
resource "terraform_data" "by_each" {
  for_each = var.subnets
  input = {
    name = each.key
    cidr = each.value.cidr
    az   = each.value.az
  }
}
```

Inside a `for_each` block you get `each.key` and `each.value` instead of `count.index`. Iterating a
map, `each.key` is the map key (`app_a`) and `each.value` is the object stored under it, so
`each.value.cidr` reaches a single attribute.

### Step 5 — Apply

```bash
terraform apply -auto-approve
```

**Expected output**

```text
Apply complete! Resources: 5 added, 0 changed, 0 destroyed.

Outputs:

count_addresses = [
  "web",
  "api",
  "web",
]
each_addresses = {
  "app_a" = "10.0.1.0/24"
  "app_b" = "10.0.2.0/24"
}
list_has_duplicates = tolist([
  "web",
  "api",
  "web",
])
set_removed_duplicates = tolist([
  "us-east-2a",
  "us-east-2b",
])
```

Five resources from two resource blocks: three from `count`, two from `for_each`.

### Step 6 — Compare list against set in the outputs

Look at the last two outputs above. `list_has_duplicates` kept both copies of `web`, in the order you
wrote them. `set_removed_duplicates` has only two zones even though the variable listed three — the
set discarded the repeat. A set also has no inherent order, which is why that output wraps it in
`sort()` to get a result you can rely on.

```bash
terraform output set_removed_duplicates
```

**Expected output**

```text
tolist([
  "us-east-2a",
  "us-east-2b",
])
```

### Step 7 — Compare the two kinds of address

```bash
terraform state list
```

**Expected output**

```text
terraform_data.by_count[0]
terraform_data.by_count[1]
terraform_data.by_count[2]
terraform_data.by_each["app_a"]
terraform_data.by_each["app_b"]
```

`count` produced numeric addresses in square brackets. `for_each` produced string keys. This is the
difference that matters operationally, and the next four steps show why.

### Step 8 — Inspect one `count` instance

```bash
terraform state show 'terraform_data.by_count[0]'
```

**Expected output**

```text
# terraform_data.by_count[0]:
resource "terraform_data" "by_count" {
    id     = "1ef69e02-068b-9417-c605-633c99e4bafc"
    input  = "web"
    output = "web"
}
```

The quotes around the address matter, because your shell would otherwise try to interpret the square
brackets. Note what identifies this instance: nothing but its position. Index `0` happens to hold
`web` today.

### Step 9 — Inspect one `for_each` instance

```bash
terraform state show 'terraform_data.by_each["app_a"]'
```

**Expected output**

```text
# terraform_data.by_each["app_a"]:
resource "terraform_data" "by_each" {
    id     = "61c52b34-da95-6ebc-6c01-1a4001aaf599"
    input  = {
        az   = "us-east-2a"
        cidr = "10.0.1.0/24"
        name = "app_a"
    }
    output = {
        az   = "us-east-2a"
        cidr = "10.0.1.0/24"
        name = "app_a"
    }
}
```

This instance is identified by the key `app_a`, which came from your data rather than from ordering.
That binding between key and instance is what survives a change to the input.

### Step 10 — Shorten the list, and watch the damage

Remove the middle entry (`api`) from the list and plan:

```bash
terraform plan -var 'tag_names=["web","web"]'
```

**Expected output**

```text
Terraform will perform the following actions:

  # terraform_data.by_count[1] will be updated in-place
  ~ resource "terraform_data" "by_count" {
        id     = "bc5997a0-7b75-40b6-fefe-b06de20d2554"
      ~ input  = "api" -> "web"
      ~ output = "api" -> (known after apply)
    }

  # terraform_data.by_count[2] will be destroyed
  # (because index [2] is out of range for count)
  - resource "terraform_data" "by_count" {
      - id     = "2c9c0082-c4ba-c4a7-8ba4-6dc9b16dfd35" -> null
      - input  = "web" -> null
      - output = "web" -> null
    }

Plan: 0 to add, 1 to change, 1 to destroy.
```

You deleted one item and two resources are affected. Read the reason Terraform prints for itself:
index `[2]` is now out of range, so it is destroyed, and index `[1]` is rewritten from `api` to `web`
because everything after the removed item shifted down a slot. With real infrastructure that means
modifying and rebuilding servers you never intended to touch.

### Step 11 — Shorten the map, and see the difference

Now remove one entry from the map:

```bash
terraform plan -var 'subnets={app_a={cidr="10.0.1.0/24",az="us-east-2a"}}'
```

**Expected output**

```text
Terraform will perform the following actions:

  # terraform_data.by_each["app_b"] will be destroyed
  # (because key ["app_b"] is not in for_each map)
  - resource "terraform_data" "by_each" {
      - id     = "a8373c0b-225e-3082-138d-50a8000bfc43" -> null
      - input  = {
          - az   = "us-east-2b"
          - cidr = "10.0.2.0/24"
          - name = "app_b"
        } -> null
      - output = {
          - az   = "us-east-2b"
          - cidr = "10.0.2.0/24"
          - name = "app_b"
        } -> null
    }

Plan: 0 to add, 0 to change, 1 to destroy.
```

Exactly one resource is destroyed, and Terraform's reason is precise: the key `app_b` is no longer in
the map. `app_a` keeps its key, so it is not mentioned at all.

### Step 12 — Compare the two plans

Put the two summary lines next to each other. Removing one list item gave
`0 to add, 1 to change, 1 to destroy`. Removing one map entry gave
`0 to add, 0 to change, 1 to destroy`. Same size of edit, one extra resource disturbed by `count`.

The rule that follows: prefer `for_each` with a map or set whenever the items have a natural identity
— a name, a key, an environment — so an instance keeps its address when its neighbours change. Keep
`count` for cases that genuinely are "N interchangeable copies", where position carries no meaning.

### Step 13 — Destroy

```bash
terraform destroy -auto-approve
```

**Expected output**

```text
Destroy complete! Resources: 5 destroyed.
```

## Done when

- [ ] You can state the difference between list, set, and map in one sentence each
- [ ] `apply` creates five resources from two resource blocks
- [ ] `set_removed_duplicates` shows two zones, not three
- [ ] `state list` shows `[0]` style addresses for `count` and `["app_a"]` style for `for_each`
- [ ] `state show` worked on both an indexed and a keyed address
- [ ] Shortening the list reported `1 to change, 1 to destroy`
- [ ] Shortening the map reported `0 to change, 1 to destroy`
- [ ] You can say why `for_each` is the safer default

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `Invalid value for input variable` | Type does not match the declaration | Match the shape in `variables.tf`, including every object attribute |
| `no matches found: terraform_data.by_count[0]` | Shell expanded the brackets | Quote the address: `'terraform_data.by_count[0]'` |
| `each.key is not supported` | `each` used inside a `count` block, or the reverse | `count` uses `count.index`; `for_each` uses `each.key` |
| `Invalid for_each argument` | Passed a list to `for_each` | Wrap it: `for_each = toset(var.my_list)` |
| `this object has no attribute cidr` | Missing an attribute in a map value | Every map entry needs both `cidr` and `az` |
| `must be accessed on specific instances` | Referenced a `count` resource without an index | Use `[0]` or `[*]` |
| Duplicates unexpectedly gone | Variable declared as `set` rather than `list` | Change the `type` to `list(string)` |

## Cleanup

```bash
terraform destroy -auto-approve
```

## Next steps

- Deep dive: [docs/05-variables.md](../docs/05-variables.md)
- Visual: [html/intermediate.html](../html/intermediate.html)
- Continue to [Lab 12 — Functions](lab12-functions.md)
