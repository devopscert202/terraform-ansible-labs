# Collections and Functions

Backs labs 11 and 12. Covers the three collection types and why the difference matters,
`count` versus `for_each`, and the built-in functions worth knowing. Generating nested blocks from
the same kind of data is [`14-dynamic-blocks.md`](14-dynamic-blocks.md) at lab21; running the same
`count` versus `for_each` comparison against real AWS resources is
[`16-count-foreach.md`](16-count-foreach.md) at lab24.

## The problem both solve

Every lab before these two wrote one block per object. Three subnets meant three `aws_subnet` blocks,
nearly identical. That does not scale, and it does not survive review — a typo in the third copy is
invisible.

| Lab | Tool | Turns |
|---|---|---|
| lab11 | Collection types and `for` expressions | One collection into another, and a map entry into a real subnet |
| lab12 | Built-in functions | Raw input values into the shape you actually need |
| lab21 | `dynamic` blocks | One nested block into many nested blocks |
| lab24 | `count` and `for_each` again | The same two blocks into real S3 buckets, where a bad plan costs something |

All three run at **plan time**, on your machine, before any API call. Nothing here is a runtime
loop; it is Terraform expanding your configuration into a concrete set of resources.

**Visual summary:** [`../html/concepts.html`](../html/concepts.html)

## Collection types (lab11)

Three types look similar in HCL and behave very differently.

| Type | Ordered? | Duplicates? | Addressed by | Declared as |
|---|---|---|---|---|
| **list** | Yes, order preserved | Yes, kept | Position — `[0]`, `[1]` | `list(string)` |
| **set** | No, order not meaningful | No, silently dropped | Not addressable by position | `set(string)` |
| **map** | No | Keys unique by definition | String key — `["app_a"]` | `map(string)`, `map(object({...}))` |

Lab11 declares one of each so the differences are visible in the output:

```hcl
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

The list keeps both copies of `web` and keeps its order. The set silently drops the repeated
`us-east-2a` and leaves you two elements — note that the *declared type* did the deduplication, not
a function call. The map holds a structured object per key, which is the shape `for_each` most
wants.

Lab11 does not stop at printing them. It indexes the map by key and hands the result to a real
resource:

```hcl
resource "aws_subnet" "app_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.subnets["app_a"].cidr
  availability_zone = var.subnets["app_a"].az
}
```

That is one `resource` block and therefore one subnet, even though the map holds two entries.
Producing one subnet per entry needs `for_each`, which lab24 teaches; until then, name the key you
want. The payoff is that the map value is load-bearing — edit `app_a`'s CIDR and a real subnet moves
— while the address `aws_subnet.app_a` stays stable no matter what happens to `app_b`.

`us-east-2` has three availability zones, `us-east-2a` through `us-east-2c`, so a set of zone names
here has at most three distinct members. `var.availability_zones` is a literal set used only to
demonstrate set behaviour, but `var.subnets[*].az` is not: lab11 passes it straight to
`availability_zone`, so an invalid zone name there fails at apply with
`InvalidParameterValue`.

Because a set has no meaningful order, printing one reproducibly needs a sort:

```hcl
output "set_removed_duplicates" {
  description = "The set dropped the repeated zone. sort() gives a stable order."
  value       = sort(tolist(var.availability_zones))
}
```

`tolist` converts the set to a list so `sort` can order it.

## count versus for_each (lab24)

Both create multiple instances from one block. Choosing wrongly causes real damage, so this is
worth getting right the first time.

Neither appears in lab11's configuration — the track deliberately withholds them until lab24, so
that the collection types are learned before the meta-arguments that consume them. Read this section
now for the shape of the problem; lab24 is where you run it.

```hcl
# count makes copies addressed by number: terraform_data.by_count[0], [1], [2].
resource "terraform_data" "by_count" {
  count = length(var.tag_names)
  input = var.tag_names[count.index]
}

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

| | `count` | `for_each` |
|---|---|---|
| Takes | A number | A map or a set of strings |
| Iteration variable | `count.index` (0, 1, 2…) | `each.key` and `each.value` |
| Address | `terraform_data.by_count[0]` | `terraform_data.by_each["app_a"]` |
| Address stability | **Tied to position** | **Tied to key** |

### Why `count` is dangerous

State addresses come from the index. Remove the middle element of a three-item list and everything
after it shifts down:

```
before:  [0]=web   [1]=api   [2]=db
remove "api"
after:   [0]=web   [1]=db
```

Terraform sees `[1]` change from `api` to `db`, and `[2]` disappear. It plans to **modify or
replace `[1]` and destroy `[2]`** — when all you asked for was to remove one thing. On real
infrastructure that is a rebuilt database.

`for_each` has no such failure. Removing the `app_a` key destroys `["app_a"]` and touches nothing
else, because each address is bound to its key rather than its position.

**Use `for_each` for anything named or persistent.** Reach for `count` only for genuinely
interchangeable, positionally identical copies, or as a conditional
(`count = var.enabled ? 1 : 0`).

Lab11 shows the *addressing* half of this lesson without the meta-arguments: shortening
`var.subnets` leaves `aws_subnet.app_a` untouched, because a key survives its neighbours' removal,
whereas a positional reference would have repointed a real subnet at a different CIDR. Lab24 runs
the full experiment on S3 buckets and captures both plans:
`1 to add, 0 to change, 2 to destroy` for the list, `0 to add, 0 to change, 2 to destroy` for the
map. That comparison is [`16-count-foreach.md`](16-count-foreach.md).

### Feeding a set to for_each

`for_each` accepts a map or a set of strings, not a list. Convert a list with `toset`:

```hcl
resource "aws_subnet" "example" {
  for_each   = toset(["10.0.1.0/24", "10.0.2.0/24"])
  vpc_id     = aws_vpc.this.id
  cidr_block = each.value
}
```

With a set, `each.key` and `each.value` are the same string. Be aware that the *value* becomes the
address — so changing a CIDR here replaces that subnet, which is usually what you want anyway.

## Functions (lab12)

Terraform ships a fixed library of built-in functions. You cannot define your own. They are pure
transformations, evaluated at plan time.

Lab12 computes every value with a function and then *uses* the results: `local.subnet_prefix` becomes
a real subnet's `cidr_block`, and `local.unique_cidrs` becomes a real security group's ingress
ranges. The resources are free, but they are in AWS, so the arithmetic has consequences:

```hcl
locals {
  # String functions: force lowercase, then swap spaces for hyphens.
  slug = lower(replace(var.application, " ", "-"))

  # Collection functions: toset() drops duplicates, sort() gives a stable order.
  unique_cidrs = sort(tolist(toset(var.cidrs)))

  # Numeric and network functions.
  cidr_count    = length(local.unique_cidrs)
  subnet_prefix = cidrsubnet("10.20.0.0/16", 8, 12)

  # Encoding functions: build a JSON string from a Terraform object.
  config_json = jsonencode({
    name  = local.slug
    cidrs = local.unique_cidrs
  })

  # Formatting: build a display string from several values.
  summary = format("%s uses %d unique CIDR(s)", local.slug, local.cidr_count)
}
```

| Expression | Input | Result |
|---|---|---|
| `lower(replace("Payments API", " ", "-"))` | `"Payments API"` | `"payments-api"` |
| `sort(tolist(toset([...])))` | `["10.0.2.0/24","10.0.1.0/24","10.0.1.0/24"]` | `["10.0.1.0/24","10.0.2.0/24"]` |
| `length(...)` | that 2-element list | `2` |
| `cidrsubnet("10.20.0.0/16", 8, 12)` | a /16 | `"10.20.12.0/24"` |
| `jsonencode({...})` | an object | a JSON string |
| `format("%s uses %d unique CIDR(s)", ...)` | slug and count | `"payments-api uses 2 unique CIDR(s)"` |

Note the reading direction: `sort(tolist(toset(x)))` evaluates innermost first — dedupe, convert to
list, then sort.

`cidrsubnet` is the one worth dwelling on. `cidrsubnet(prefix, newbits, netnum)` carves a subnet
out of a larger range: add `newbits` bits to the prefix length, then take subnet number `netnum`.
So `cidrsubnet("10.20.0.0/16", 8, 12)` gives a `/24` (16 + 8) and takes the 12th one, yielding
`10.20.12.0/24`. This is how you avoid hand-calculating CIDR blocks and getting them subtly wrong.

### Functions worth knowing

| Category | Functions |
|---|---|
| String | `lower`, `upper`, `replace`, `trimspace`, `split`, `join`, `format`, `substr`, `startswith`, `endswith` |
| Collection | `length`, `merge`, `keys`, `values`, `lookup`, `contains`, `concat`, `flatten`, `sort`, `distinct`, `element`, `coalesce`, `one` |
| Type conversion | `tostring`, `tonumber`, `tolist`, `toset`, `tomap`, `try`, `can` |
| Numeric | `min`, `max`, `abs`, `ceil`, `floor`, `parseint` |
| Network | `cidrsubnet`, `cidrsubnets`, `cidrhost`, `cidrnetmask` |
| Encoding | `jsonencode`, `jsondecode`, `base64encode`, `base64decode`, `yamlencode`, `yamldecode` |
| Filesystem | `file`, `templatefile`, `pathexpand`, `fileexists` |
| Date | `timestamp`, `timeadd`, `formatdate` |

Two to use with care. `timestamp()` changes on every run, so anything derived from it produces a
permanent diff — never put it in a resource argument. And `file()` reads at plan time, so the file
must exist on whichever machine plans, including your CI runner.

### terraform console

The fastest way to learn any of these is to try it:

```bash
cd terraform/labs/lab12-functions
terraform init
terraform console
```

```text
> lower("Hello World")
"hello world"
> cidrsubnet("10.0.0.0/16", 8, 1)
"10.0.1.0/24"
> toset(["a", "b", "a"])
toset([
  "a",
  "b",
])
> length(var.cidrs)
3
```

`console` has full access to your variables, locals, resources, and state. It reads and never
writes, so nothing you type can change infrastructure. Exit with `exit` or Ctrl-D.

## for expressions

Distinct from `for_each` — a `for` expression transforms one collection into another, inside an
expression:

```hcl
# list -> list
[for name in var.tag_names : upper(name)]

# map -> map, reading a resource's attributes
{ for key, item in terraform_data.by_each : key => item.output.cidr }

# list -> list, with a filter
[for rule in values(var.ingress_rules) : rule.port if rule.port != 22]
```

Square brackets produce a list, braces produce a map — and a map needs the `key => value` arrow.
Lab11's `subnet_cidrs` output uses exactly this to project a map of subnet objects down to the one
attribute a `cidr_block` argument needs.

The splat operator is a shorthand for the simplest list case:

```hcl
terraform_data.by_count[*].output          # equivalent to [for r in ... : r.output]
```

## Command reference

```bash
cd terraform/labs/lab11-collections
terraform init
terraform apply
terraform state list      # terraform_data, aws_vpc.main, aws_subnet.app_a
terraform output          # app_a_subnet_from_map: requested vs actual
terraform destroy

cd ../lab12-functions
terraform init
terraform console         # try: cidrsubnet("10.0.0.0/16", 8, 1)
terraform apply           # VPC + subnet at the cidrsubnet() result + security group
```

## Where next

- The same data-driven idea applied to nested blocks, at lab21:
  [`14-dynamic-blocks.md`](14-dynamic-blocks.md)
- `count` versus `for_each` again, on real S3 buckets where the plan has consequences, at lab24:
  [`16-count-foreach.md`](16-count-foreach.md)
- Using these patterns in a full build: [`08-capstone.md`](08-capstone.md)

## Hands-On Labs

| Lab | Description |
|---|---|
| [Lab 11: Collections](../labmanuals/lab11-collections.md) | list vs set vs map, `for` expressions, and a real subnet built from a map entry read by key |
| [Lab 12: Functions](../labmanuals/lab12-functions.md) | String, collection, CIDR, encoding and format functions, `terraform console`, and a real subnet at the `cidrsubnet()` result |
