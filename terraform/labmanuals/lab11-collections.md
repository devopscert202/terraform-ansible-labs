# Lab 11 — Collections

| | |
|---|---|
| **Goal** | Tell list, set, and map apart, convert between them, and reshape them with `for` expressions — then read the results back out of state. |
| **Time** | 40–50 minutes |
| **Tier** | Intermediate |
| **Files** | `terraform/labs/lab11-collections/` |

## Overview

So far your variables held one value each. A **collection type** holds several. HCL has three that
matter: a **list** is ordered and allows duplicates, addressed by position (`0`, `1`, `2`); a **set**
is unordered and silently drops duplicates; a **map** is a set of key/value pairs addressed by a
string key. You met all three in Lab 06 as declared types. This lab is about working with the
values inside them.

The tool for that is the **`for` expression**: a small piece of syntax that reads one collection and
produces another, optionally transforming or filtering as it goes. `[for x in list : upper(x)]`
gives you a new list. `{for k, v in map : k => v.cidr}` gives you a new map. Add an `if` clause and
you get a filter. Every reshaping problem you will meet in Terraform — building a tag map, pulling
one attribute out of a map of objects, selecting the subnets in one zone — is a `for` expression.

Making many *copies of a resource* from a collection is a different job, done by the `count` and
`for_each` meta-arguments. Those come later, in [Lab 24](lab24-count-foreach-buckets.md), against
real S3 buckets. This lab stays on the values themselves.

The one resource here is `terraform_data`, a built-in placeholder that creates nothing in any cloud,
so this lab is free and needs no AWS credentials.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `var.tag_names` | A `list(string)` with a deliberate duplicate | Free |
| `var.availability_zones` | A `set(string)` with a duplicate that gets dropped | Free |
| `var.subnets` | A `map(object(...))` of subnet definitions | Free |
| 6 locals | Conversions and `for` expressions over all three types | Free |
| `terraform_data.collections` | One placeholder resource holding the measured shapes in state | Free |
| 7 outputs | The result of each conversion and each `for` expression | Free |

One managed resource, no data sources.

## Before you start

- [ ] Lab 10 completed ([lab10-capstone-vpc-ec2.md](lab10-capstone-vpc-ec2.md))
- [ ] You have seen `list(string)`, `set(string)`, and `map(string)` declared in Lab 06
- [ ] You have used `terraform console` — Lab 06 introduced it, and Step 3 here is a refresher
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

`tag_names` contains `web` twice. `availability_zones` also lists a value twice — but it is declared
`set(string)`, so Terraform drops the repeat while reading the default. `subnets` is a map whose
values are objects, each with two named attributes of declared types.

### Step 2 — Initialize

There is no provider in this configuration, but `terraform console` and `terraform plan` still
require an initialized directory.

```bash
terraform init
```

**Expected output**

```text
Terraform has been successfully initialized!
```

### Step 3 — Explore the three types in the console

`terraform console` evaluates expressions against this configuration without changing anything. Each
command below pipes one expression in and prints its result.

```bash
echo 'toset(["web","api","web"])' | terraform console
echo 'length(var.availability_zones)' | terraform console
echo 'keys(var.subnets)' | terraform console
echo 'var.tag_names[1]' | terraform console
echo 'var.subnets["app_a"].cidr' | terraform console
```

**Expected output**

```text
toset([
  "api",
  "web",
])
2
tolist([
  "app_a",
  "app_b",
])
"api"
"10.0.1.0/24"
```

Read those five results in order. Three strings went into `toset()` and two came out, sorted rather
than in the order typed. `var.availability_zones` has length `2` for the same reason, although its
default lists three zones. `keys()` returns a map's keys as a list. A list element is reached by
number, `var.tag_names[1]`; a map value is reached by key, then by attribute name.

A set cannot be indexed at all — there is no `[0]` to ask for. Convert it with `tolist()` first, and
wrap that in `sort()` if you need a repeatable order.

### Step 4 — Read the locals that do the reshaping

```bash
sed -n '/^locals {/,/^}/p' main.tf
```

**Expected output**

```text
locals {
  # toset() discards the duplicate the list keeps; sort() gives a stable order,
  # because a set has no order of its own.
  unique_tag_names = sort(tolist(toset(var.tag_names)))

  # A for expression over a list produces a list, still addressed by position.
  tag_labels = [for name in var.tag_names : upper(name)]

  # A for expression over a map produces a map. name is the key, subnet is the
  # object stored under it, so subnet.cidr reaches a single attribute.
  subnet_cidrs = { for name, subnet in var.subnets : name => subnet.cidr }

  # An if clause at the end of a for expression filters the result.
  zone_a_subnets = [for name, subnet in var.subnets : name if subnet.az == "us-east-2a"]

  # The three collection types side by side, counted the same way.
  collection_shapes = {
    list_length   = length(var.tag_names)
    set_length    = length(var.availability_zones)
    map_length    = length(var.subnets)
    map_keys      = keys(var.subnets)
    list_index_1  = var.tag_names[1]
    map_key_app_a = var.subnets["app_a"].cidr
  }
}
```

Five locals plus the summary map. The next three steps take the three `for` expressions one at a
time.

### Step 5 — A `for` expression over a list

Square brackets around a `for` produce a **list**, one output element per input element, in the same
order.

```bash
echo '[for name in var.tag_names : upper(name)]' | terraform console
```

**Expected output**

```text
[
  "WEB",
  "API",
  "WEB",
]
```

Three in, three out. The duplicate `web` was transformed twice and both copies survive, because a
list preserves order and repetition. This is `local.tag_labels`.

### Step 6 — A `for` expression over a map

Curly braces and a `=>` between key and value produce a **map**. Iterating a map gives you two
loop variables: the key first, then the value.

```bash
echo 'local.subnet_cidrs' | terraform console
```

**Expected output**

```text
{
  "app_a" = "10.0.1.0/24"
  "app_b" = "10.0.2.0/24"
}
```

The keys came through unchanged and each object value was reduced to one of its attributes. This is
the most common shape in real configurations: you hold rich objects in a variable and project out
the one field a particular resource argument needs.

### Step 7 — Filter with an `if` clause

An `if` at the end of a `for` expression drops the elements whose condition is false.

```bash
echo 'local.zone_a_subnets' | terraform console
```

**Expected output**

```text
[
  "app_a",
]
```

`app_b` is in `us-east-2b`, so the condition `subnet.az == "us-east-2a"` was false for it and it
never reached the result. Note that this expression iterates a map but is wrapped in square
brackets, so the result is a list of keys, not a map.

### Step 8 — Read the one resource

```bash
sed -n '/^# One resource block/,$p' main.tf
```

**Expected output**

```text
# One resource block, one instance. Turning a collection into many copies of a
# resource needs the count and for_each meta-arguments, which Lab 24 introduces.
resource "terraform_data" "collections" {
  input = local.collection_shapes
}
```

One resource block and one instance. `terraform_data` stores whatever you put in `input` and echoes
it back as `output`, which is exactly what is needed here: a way to push the measured shapes through
a real apply and read them back out of state.

### Step 9 — Apply

```bash
terraform apply -auto-approve
```

**Expected output**

```text
terraform_data.collections: Creating...
terraform_data.collections: Creation complete after 0s [id=986ba9e0-f6d6-80e7-3e64-013bd2aa2488]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

collection_shapes = {
  "list_index_1" = "api"
  "list_length" = 3
  "map_key_app_a" = "10.0.1.0/24"
  "map_keys" = tolist([
    "app_a",
    "app_b",
  ])
  "map_length" = 2
  "set_length" = 2
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
subnet_cidrs = {
  "app_a" = "10.0.1.0/24"
  "app_b" = "10.0.2.0/24"
}
tag_labels = [
  "WEB",
  "API",
  "WEB",
]
unique_tag_names = tolist([
  "api",
  "web",
])
zone_a_subnets = [
  "app_a",
]
```

Your `id` will differ; it is a UUID generated locally. One resource, seven outputs.

### Step 10 — Compare list against set in the outputs

Look at two of those outputs side by side.

```bash
terraform output list_has_duplicates
terraform output set_removed_duplicates
terraform output unique_tag_names
```

**Expected output**

```text
tolist([
  "web",
  "api",
  "web",
])
tolist([
  "us-east-2a",
  "us-east-2b",
])
tolist([
  "api",
  "web",
])
```

`list_has_duplicates` kept both copies of `web`, in the order they were written.
`set_removed_duplicates` shows two zones although the variable listed three — the set discarded the
repeat at declaration time. `unique_tag_names` is the same list from the first output after
`toset()` removed its duplicate and `sort()` put what remained in a repeatable order; note that
`web` now comes second, not first.

Choose a `list` when order or repetition carries meaning, a `set` when the values are a membership
question ("which zones?"), and a `map` when each value needs a name you look it up by.

### Step 11 — Read the shapes back out of state

```bash
terraform state list
terraform state show terraform_data.collections
```

**Expected output**

```text
terraform_data.collections
# terraform_data.collections:
resource "terraform_data" "collections" {
    id     = "986ba9e0-f6d6-80e7-3e64-013bd2aa2488"
    input  = {
        list_index_1  = "api"
        list_length   = 3
        map_key_app_a = "10.0.1.0/24"
        map_keys      = [
            "app_a",
            "app_b",
        ]
        map_length    = 2
        set_length    = 2
    }
    output = {
        list_index_1  = "api"
        list_length   = 3
        map_key_app_a = "10.0.1.0/24"
        map_keys      = [
            "app_a",
            "app_b",
        ]
        map_length    = 2
        set_length    = 2
    }
}
```

`list_length` is `3` and `set_length` is `2`, from defaults that both listed three entries. That one
pair of numbers is the whole list-versus-set lesson, now recorded in a state file.

### Step 12 — Change an input and watch every dependent value move

Nothing is applied here — `plan` only reports. Shorten the list to two entries:

```bash
terraform plan -var 'tag_names=["web","web"]'
```

**Expected output** *(trimmed)*

```text
  # terraform_data.collections will be updated in-place
  ~ resource "terraform_data" "collections" {
        id     = "986ba9e0-f6d6-80e7-3e64-013bd2aa2488"
      ~ input  = {
          ~ list_index_1  = "api" -> "web"
          ~ list_length   = 3 -> 2
            # (4 unchanged attributes hidden)
        }
      ...
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```

Two things changed from one edit. `list_length` fell to `2`, which is expected. `list_index_1`
changed from `api` to `web`, which is the part worth noticing: removing the middle element shifted
everything after it down one position, so index `1` now holds a different value. Positional
addressing is fragile in exactly this way.

Now shorten the map instead:

```bash
terraform plan -var 'subnets={app_a={cidr="10.0.1.0/24",az="us-east-2a"}}'
```

**Expected output** *(trimmed)*

```text
      ~ input  = {
          ~ map_length    = 2 -> 1
            # (4 unchanged attributes hidden)
        }
      ...

Plan: 0 to add, 1 to change, 0 to destroy.

Changes to Outputs:
  ~ subnet_cidrs           = {
      - app_b = "10.0.2.0/24"
        # (1 unchanged attribute hidden)
    }
```

`map_key_app_a` is untouched, and `subnet_cidrs` loses exactly the entry you removed. `app_a` keeps
its key no matter what happens to its neighbours, because a key is part of your data rather than a
consequence of ordering.

Keep that contrast in mind: it is the same reason [Lab 24](lab24-count-foreach-buckets.md) prefers
`for_each` over a map to `count` over a list when creating many copies of a resource.

### Step 13 — Destroy

```bash
terraform destroy -auto-approve
```

**Expected output**

```text
terraform_data.collections: Destroying... [id=986ba9e0-f6d6-80e7-3e64-013bd2aa2488]
terraform_data.collections: Destruction complete after 0s

Destroy complete! Resources: 1 destroyed.
```

## Done when

- [ ] You can state the difference between list, set, and map in one sentence each
- [ ] `toset(["web","api","web"])` returned two elements, sorted
- [ ] `apply` created one resource and printed seven outputs
- [ ] `set_removed_duplicates` shows two zones, not three
- [ ] The list `for` expression returned `["WEB","API","WEB"]` — three elements, order preserved
- [ ] The map `for` expression returned a map keyed `app_a` and `app_b`
- [ ] The `if` clause left only `app_a`
- [ ] `state show` reported `list_length = 3` beside `set_length = 2`
- [ ] Shortening the list moved `list_index_1`; shortening the map did not move `map_key_app_a`
- [ ] `terraform destroy` reports `1 destroyed`

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `Invalid value for input variable` | Type does not match the declaration | Match the shape in `variables.tf`, including every object attribute |
| `Invalid index` on a set | Sets have no positions | `tolist(var.availability_zones)[0]`, or use a list |
| `this object has no attribute cidr` | A map entry is missing an attribute | Every entry in `subnets` needs both `cidr` and `az` |
| `Invalid 'for' expression: key expression is required` | Used `{}` around a `for` without `=>` | Either use `[...]` for a list, or add `key => value` |
| `Duplicate object key` from a map `for` expression | Two input elements produced the same key | Make the key expression unique, or produce a list instead |
| Duplicates unexpectedly gone | Variable declared as `set` rather than `list` | Change the `type` to `list(string)` |
| `Reference to undeclared local value` | Used `local.x` before adding it to the `locals` block | Declare it in `locals` |

## Cleanup

```bash
terraform destroy -auto-approve
rm -rf .terraform terraform.tfstate*
```

## Next steps

- Deep dive: [docs/09-collections-functions.md](../docs/09-collections-functions.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab11-collections)
- Continue to [Lab 12 — Functions](lab12-functions.md)
