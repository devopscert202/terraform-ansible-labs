# Collections, Functions, and Dynamic Blocks

Deep dive for lab10, lab11, and lab12. Covers the three collection types and why the difference
matters, the built-in functions worth knowing, `count` versus `for_each`, and generating nested
blocks from data.

## The problem all three solve

Everything up to lab09 wrote one block per object. Three subnets meant three `aws_subnet` blocks,
nearly identical. That does not scale, and it does not survive review — a typo in the third copy is
invisible.

These three labs are the three ways out:

| Lab | Tool | Turns |
|---|---|---|
| lab10 | `count` and `for_each` | One resource block into many resource instances |
| lab11 | Built-in functions | Raw input values into the shape you actually need |
| lab12 | `dynamic` blocks | One nested block into many nested blocks |

All three run at **plan time**, on your machine, before any API call. Nothing here is a runtime
loop; it is Terraform expanding your configuration into a concrete set of resources.

**Visual summary:** [`../../html/advanced.html`](../../html/advanced.html)

## Collection types (lab10)

Three types look similar in HCL and behave very differently.

| Type | Ordered? | Duplicates? | Addressed by | Declared as |
|---|---|---|---|---|
| **list** | Yes, order preserved | Yes, kept | Position — `[0]`, `[1]` | `list(string)` |
| **set** | No, order not meaningful | No, silently dropped | Not addressable by position | `set(string)` |
| **map** | No | Keys unique by definition | String key — `["app_a"]` | `map(string)`, `map(object({...}))` |

Lab10 declares one of each so the differences are visible in the output:

```hcl
variable "tag_names" {
  type        = list(string)
  description = "A list: ordered, duplicates allowed, indexed by number."
  default     = ["web", "api", "web"]
}

variable "availability_zones" {
  type        = set(string)
  description = "A set: unordered, duplicates removed automatically."
  default     = ["us-east-1a", "us-east-1b", "us-east-1a"]
}

variable "subnets" {
  type        = map(object({ cidr = string, az = string }))
  description = "A map: each value is looked up by a string key instead of a number."
  default = {
    app_a = { cidr = "10.0.1.0/24", az = "us-east-1a" }
    app_b = { cidr = "10.0.2.0/24", az = "us-east-1b" }
  }
}
```

The list keeps both copies of `web` and keeps its order. The set silently drops the repeated
`us-east-1a` and leaves you two elements — note that the *declared type* did the deduplication, not
a function call. The map holds a structured object per key, which is the shape `for_each` most
wants.

Because a set has no meaningful order, printing one reproducibly needs a sort:

```hcl
output "set_removed_duplicates" {
  description = "The set dropped the repeated zone. sort() gives a stable order."
  value       = sort(tolist(var.availability_zones))
}
```

`tolist` converts the set to a list so `sort` can order it.

## count versus for_each (lab10)

Both create multiple instances from one block. Choosing wrongly causes real damage, so this is
worth getting right the first time.

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

## Functions (lab11)

Terraform ships a fixed library of built-in functions. You cannot define your own. They are pure
transformations, evaluated at plan time.

Lab11 creates no resources at all — every value is a function result, so it runs free and needs no
credentials:

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
cd terraform/labs/lab11-functions
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
Lab10's output uses exactly this to turn a set of resource instances into a keyed map of their
values.

The splat operator is a shorthand for the simplest list case:

```hcl
terraform_data.by_count[*].output          # equivalent to [for r in ... : r.output]
```

## Dynamic blocks (lab12)

`for_each` on a resource makes many resources. A `dynamic` block makes many **nested blocks inside
one resource** — which is what a security group's `ingress` rules need.

```hcl
variable "ingress_rules" {
  type = map(object({
    port        = number
    cidr_blocks = list(string)
    description = string
  }))
  description = "One entry per inbound rule. dynamic turns each entry into an ingress block."
  default = {
    ssh = {
      port        = 22
      cidr_blocks = ["10.0.0.0/8"]
      description = "internal SSH"
    }
    http = {
      port        = 80
      cidr_blocks = ["10.0.0.0/8"]
      description = "internal HTTP"
    }
    https = {
      port        = 443
      cidr_blocks = ["10.0.0.0/8"]
      description = "internal HTTPS"
    }
  }
}

resource "aws_security_group" "service" {
  name_prefix = "lab12-dynamic-"
  description = "Ingress rules generated by a dynamic block"

  # One ingress block is generated per entry in var.ingress_rules.
  dynamic "ingress" {
    for_each = var.ingress_rules

    content {
      description = ingress.value.description
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = "tcp"
      cidr_blocks = ingress.value.cidr_blocks
    }
  }

  # A single static block, written the ordinary way, for comparison.
  egress {
    description = "all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "lab12-dynamic-sg"
    Lab  = "lab12"
  }
}
```

| Element | Meaning |
|---|---|
| `dynamic "ingress"` | The label names the nested block type to generate. It must be a block the resource genuinely supports |
| `for_each` | The collection to iterate. Map or set, same as on a resource |
| `content { }` | The body of each generated block. Required — the arguments go here, not directly in `dynamic` |
| `ingress.value` | The current element. **The iterator is named after the block**, not `each` |
| `ingress.key` | The current map key — `"ssh"`, `"http"`, `"https"` |

The iterator naming is the detail that catches people: inside `dynamic "ingress"` you write
`ingress.value`, not `each.value`. Override it with `iterator = rule` if the default name collides.

Adding a fourth rule now means adding a map entry — no HCL structure changes, and the diff in
review is one readable block of data. That is the real gain: the security policy becomes data you
can read, rather than structure you have to parse.

### When not to use dynamic

`dynamic` costs readability. HashiCorp's own guidance is to prefer writing blocks out literally
when you can, and use `dynamic` only when the collection is genuinely variable — supplied by a
caller, or differing per environment. Two or three fixed rules are clearer written plainly.

Also keep in mind that `dynamic` only generates **blocks**, never arguments. `for_each` on a
resource and `dynamic` inside one are different tools and are not interchangeable.

## Command reference

```bash
cd terraform/labs/lab10-collections
terraform init
terraform apply
terraform state list      # note [0]/[1] from count vs ["app_a"] from for_each
terraform output
terraform destroy

cd ../lab11-functions
terraform init
terraform console         # try: cidrsubnet("10.0.0.0/16", 8, 1)
terraform apply           # creates nothing; every output is a function result

cd ../lab12-dynamic-blocks
terraform init
terraform plan            # count the generated ingress blocks
terraform plan -var='ingress_rules={admin={port=8443,cidr_blocks=["10.0.0.0/8"],description="admin UI"}}'
```

## Where next

- Using these patterns in a full build: [`projects.md`](projects.md), and lab21's capstone
- Escaping declarative HCL entirely, and why to avoid it: [`provisioners.md`](provisioners.md)

## Hands-On Labs

| Lab | Description |
|---|---|
| [Lab 10: Collections](../../labmanuals/lab10-collections.md) | list vs set vs map, `count` vs `for_each`, address stability |
| [Lab 11: Functions](../../labmanuals/lab11-functions.md) | String, collection, CIDR, encoding and format functions, `terraform console` |
| [Lab 12: Dynamic Blocks](../../labmanuals/lab12-dynamic-blocks.md) | Generate security group `ingress` blocks from a variable |
