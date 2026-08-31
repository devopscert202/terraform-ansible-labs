# Lab 11 — Collections

| | |
|---|---|
| **Goal** | Tell list, set, and map apart, convert between them, reshape them with `for` expressions, and drive a real AWS subnet from a map entry read by key. |
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

Reshaping values is only half of it. A map earns its keep when a resource argument reads a value out
of it, so this lab also builds a real VPC and a real subnet whose `cidr_block` and
`availability_zone` come from `var.subnets["app_a"]`. Change that map entry and AWS changes with it.

Making many *copies of a resource* from a collection is a different job, done by the `count` and
`for_each` meta-arguments. That is why this lab creates **one** subnet rather than one per map
entry: `for_each` has not been taught yet. It arrives in
[Lab 24](lab24-count-foreach-buckets.md), against real S3 buckets.

A VPC and a subnet cost nothing, but they are real, so this lab needs AWS credentials.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `var.tag_names` | A `list(string)` with a deliberate duplicate | Free |
| `var.availability_zones` | A `set(string)` with a duplicate that gets dropped | Free |
| `var.subnets` | A `map(object(...))` of subnet definitions | Free |
| 7 locals | Conversions and `for` expressions over all three types, plus the tag map | Free |
| `terraform_data.collections` | A placeholder resource holding the measured shapes in state | Free |
| `aws_vpc.main` | The lab's own VPC, `10.0.0.0/16` | Free |
| `aws_subnet.app_a` | A real subnet built from `var.subnets["app_a"]` | Free |
| 10 outputs | Each conversion, each `for` expression, and the subnet AWS actually created | Free |

Three managed resources, no data sources.

## Before you start

- [ ] Lab 10 completed ([lab10-capstone-vpc-ec2.md](lab10-capstone-vpc-ec2.md))
- [ ] You have seen `list(string)`, `set(string)`, and `map(string)` declared in Lab 06
- [ ] You have used `terraform console` — Lab 06 introduced it, and Step 3 here is a refresher
- [ ] AWS credentials configured for `us-east-2` (`aws sts get-caller-identity` succeeds)
- [ ] Working directory: `../labs/lab11-collections/`

## Steps

### Step 1 — Read the three collection types

```bash
cd terraform/labs/lab11-collections
cat variables.tf
```

**Expected output**

```text
variable "aws_region" {
  type        = string
  description = "Region for the VPC and subnet. us-east-2 has zones a, b and c only."
  default     = "us-east-2"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR of the lab VPC. Every entry in var.subnets must fit inside it."
  default     = "10.0.0.0/16"
}

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
values are objects, each with two named attributes of declared types. Every variable has a default,
so no `terraform.tfvars` file is needed.

### Step 2 — Initialize

```bash
terraform init
```

**Expected output** *(trimmed)*

```text
Initializing provider plugins...
- terraform.io/builtin/terraform is built in to Terraform
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.100.0...
- Installed hashicorp/aws v5.100.0 (signed by HashiCorp)

Terraform has been successfully initialized!
```

Two providers are in play: the built-in `terraform` provider supplies `terraform_data`, and the AWS
provider supplies the VPC and subnet.

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

  common_tags = {
    Lab  = "lab11"
    Name = "lab11-collections"
  }
}
```

Five locals, the summary map, and the tag map every resource in the lab merges from. The next three
steps take the three `for` expressions one at a time.

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

### Step 8 — Read the three resources

```bash
sed -n '/^resource "terraform_data"/,$p' main.tf
```

**Expected output**

```text
resource "terraform_data" "collections" {
  input = local.collection_shapes
}

# A VPC of its own, so the lab never depends on the account having a default VPC.
resource "aws_vpc" "main" {
  cidr_block         = var.vpc_cidr
  enable_dns_support = true

  tags = local.common_tags
}

# A real subnet whose two required arguments are read out of the map by key.
# var.subnets["app_a"] selects one object; .cidr and .az reach its attributes.
# This is map indexing doing real work: change the map entry and AWS changes.
#
# One resource block is still one subnet. Creating one subnet per map entry
# needs the for_each meta-argument, which Lab 24 introduces.
resource "aws_subnet" "app_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.subnets["app_a"].cidr
  availability_zone = var.subnets["app_a"].az

  tags = merge(local.common_tags, { Name = "lab11-app-a" })
}
```

`terraform_data` stores whatever you put in `input` and echoes it back as `output`, which pushes the
measured shapes through a real apply so you can read them back out of state.

The subnet is the part to study. `var.subnets["app_a"]` indexes the map by key and returns the whole
object; `.cidr` and `.az` then reach into it for the two values AWS requires. Nothing here is
printed for its own sake — those two map values become a real subnet in a real VPC.

Note carefully what this block is **not**. It is one `resource` block, so it creates exactly one
subnet, even though `var.subnets` holds two entries. Producing one subnet per map entry requires the
`for_each` meta-argument, which [Lab 24](lab24-count-foreach-buckets.md) teaches. Until then, index
the map by key and name the entry you want.

### Step 9 — Apply

```bash
terraform apply -auto-approve
```

**Expected output**

```text

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # aws_subnet.app_a will be created
  + resource "aws_subnet" "app_a" {
      + arn                                            = (known after apply)
      + assign_ipv6_address_on_creation                = false
      + availability_zone                              = "us-east-2a"
      + availability_zone_id                           = (known after apply)
      + cidr_block                                     = "10.0.1.0/24"
      + enable_dns64                                   = false
      + enable_resource_name_dns_a_record_on_launch    = false
      + enable_resource_name_dns_aaaa_record_on_launch = false
      + id                                             = (known after apply)
      + ipv6_cidr_block_association_id                 = (known after apply)
      + ipv6_native                                    = false
      + map_public_ip_on_launch                        = false
      + owner_id                                       = (known after apply)
      + private_dns_hostname_type_on_launch            = (known after apply)
      + tags                                           = {
          + "Lab"  = "lab11"
          + "Name" = "lab11-app-a"
        }
      + tags_all                                       = {
          + "Lab"  = "lab11"
          + "Name" = "lab11-app-a"
        }
      + vpc_id                                         = (known after apply)
    }

  # aws_vpc.main will be created
  + resource "aws_vpc" "main" {
      + arn                                  = (known after apply)
      + cidr_block                           = "10.0.0.0/16"
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
          + "Lab"  = "lab11"
          + "Name" = "lab11-collections"
        }
      + tags_all                             = {
          + "Lab"  = "lab11"
          + "Name" = "lab11-collections"
        }
    }

  # terraform_data.collections will be created
  + resource "terraform_data" "collections" {
      + id     = (known after apply)
      + input  = {
          + list_index_1  = "api"
          + list_length   = 3
          + map_key_app_a = "10.0.1.0/24"
          + map_keys      = [
              + "app_a",
              + "app_b",
            ]
          + map_length    = 2
          + set_length    = 2
        }
      + output = (known after apply)
    }

Plan: 3 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + app_a_subnet_from_map  = {
      + actual_az      = "us-east-2a"
      + actual_cidr    = "10.0.1.0/24"
      + requested_az   = "us-east-2a"
      + requested_cidr = "10.0.1.0/24"
    }
  + app_a_subnet_id        = (known after apply)
  + collection_shapes      = (known after apply)
  + list_has_duplicates    = [
      + "web",
      + "api",
      + "web",
    ]
  + set_removed_duplicates = [
      + "us-east-2a",
      + "us-east-2b",
    ]
  + subnet_cidrs           = {
      + app_a = "10.0.1.0/24"
      + app_b = "10.0.2.0/24"
    }
  + tag_labels             = [
      + "WEB",
      + "API",
      + "WEB",
    ]
  + unique_tag_names       = [
      + "api",
      + "web",
    ]
  + vpc_id                 = (known after apply)
  + zone_a_subnets         = [
      + "app_a",
    ]
terraform_data.collections: Creating...
terraform_data.collections: Creation complete after 0s [id=d57e79e8-3f82-3807-d929-0f55773e1b5d]
aws_vpc.main: Creating...
aws_vpc.main: Creation complete after 4s [id=vpc-01817457dfb9c55ff]
aws_subnet.app_a: Creating...
aws_subnet.app_a: Creation complete after 1s [id=subnet-01c25594879924dc0]

Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

Outputs:

app_a_subnet_from_map = {
  "actual_az" = "us-east-2a"
  "actual_cidr" = "10.0.1.0/24"
  "requested_az" = "us-east-2a"
  "requested_cidr" = "10.0.1.0/24"
}
app_a_subnet_id = "subnet-01c25594879924dc0"
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
vpc_id = "vpc-01817457dfb9c55ff"
zone_a_subnets = [
  "app_a",
]
```

Three resources are created and ten outputs are printed. `Plan: 3 to add, 0 to change, 0 to
destroy.` Confirm that `app_a_subnet_from_map` shows `actual_cidr` equal to `requested_cidr` and
`actual_az` equal to `requested_az` — proof the map values reached AWS unchanged.

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

### Step 11 — Read the shapes and the subnet back out of state

```bash
terraform state list
terraform state show terraform_data.collections
terraform state show aws_subnet.app_a
```

**Expected output**

```text
aws_subnet.app_a
aws_vpc.main
terraform_data.collections
# terraform_data.collections:
resource "terraform_data" "collections" {
    id     = "d57e79e8-3f82-3807-d929-0f55773e1b5d"
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
# aws_subnet.app_a:
resource "aws_subnet" "app_a" {
    arn                                            = "arn:aws:ec2:us-east-2:027488552956:subnet/subnet-01c25594879924dc0"
    assign_ipv6_address_on_creation                = false
    availability_zone                              = "us-east-2a"
    availability_zone_id                           = "use2-az1"
    cidr_block                                     = "10.0.1.0/24"
    customer_owned_ipv4_pool                       = null
    enable_dns64                                   = false
    enable_lni_at_device_index                     = 0
    enable_resource_name_dns_a_record_on_launch    = false
    enable_resource_name_dns_aaaa_record_on_launch = false
    id                                             = "subnet-01c25594879924dc0"
    ipv6_cidr_block                                = null
    ipv6_cidr_block_association_id                 = null
    ipv6_native                                    = false
    map_customer_owned_ip_on_launch                = false
    map_public_ip_on_launch                        = false
    outpost_arn                                    = null
    owner_id                                       = "027488552956"
    private_dns_hostname_type_on_launch            = "ip-name"
    tags                                           = {
        "Lab"  = "lab11"
        "Name" = "lab11-app-a"
    }
    tags_all                                       = {
        "Lab"  = "lab11"
        "Name" = "lab11-app-a"
    }
    vpc_id                                         = "vpc-01817457dfb9c55ff"
}
```

`state list` reports three addresses: `aws_subnet.app_a`, `aws_vpc.main` and
`terraform_data.collections`.

In `terraform_data.collections`, `list_length` is `3` and `set_length` is `2`, from defaults that
both listed three entries. That one pair of numbers is the whole list-versus-set lesson, now
recorded in a state file.

In `aws_subnet.app_a`, `cidr_block` is `10.0.1.0/24` and `availability_zone` is `us-east-2a`. Those
values were never typed into the resource block — they were read out of the map by key.

### Step 12 — Change an input and watch every dependent value move

Nothing is applied here — `plan` only reports. Shorten the list to two entries:

```bash
terraform plan -var 'tag_names=["web","web"]'
```

**Expected output** *(trimmed)*

```text
  # terraform_data.collections will be updated in-place
  ~ resource "terraform_data" "collections" {
        id     = "d57e79e8-3f82-3807-d929-0f55773e1b5d"
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
          ~ map_keys      = [
                "app_a",
              - "app_b",
            ]
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

`aws_subnet.app_a` is absent from the plan for the same reason — it reads `var.subnets["app_a"]`, and
deleting `app_b` cannot move that key. Compare that with what a positional reference would have done:
had the subnet read `var.subnets[1]`, removing an earlier entry would have silently repointed a real
subnet at a different CIDR, and Terraform would have destroyed and recreated it.

Keep that contrast in mind: it is the same reason [Lab 24](lab24-count-foreach-buckets.md) prefers
`for_each` over a map to `count` over a list when creating many copies of a resource.

### Step 13 — Destroy

```bash
terraform destroy -auto-approve
```

**Expected output**

```text
terraform_data.collections: Refreshing state... [id=d57e79e8-3f82-3807-d929-0f55773e1b5d]
aws_vpc.main: Refreshing state... [id=vpc-01817457dfb9c55ff]
aws_subnet.app_a: Refreshing state... [id=subnet-01c25594879924dc0]

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  - destroy

Terraform will perform the following actions:

  # aws_subnet.app_a will be destroyed
  - resource "aws_subnet" "app_a" {
      - arn                                            = "arn:aws:ec2:us-east-2:027488552956:subnet/subnet-01c25594879924dc0" -> null
      - assign_ipv6_address_on_creation                = false -> null
      - availability_zone                              = "us-east-2a" -> null
      - availability_zone_id                           = "use2-az1" -> null
      - cidr_block                                     = "10.0.1.0/24" -> null
      - enable_dns64                                   = false -> null
      - enable_lni_at_device_index                     = 0 -> null
      - enable_resource_name_dns_a_record_on_launch    = false -> null
      - enable_resource_name_dns_aaaa_record_on_launch = false -> null
      - id                                             = "subnet-01c25594879924dc0" -> null
      - ipv6_native                                    = false -> null
      - map_customer_owned_ip_on_launch                = false -> null
      - map_public_ip_on_launch                        = false -> null
      - owner_id                                       = "027488552956" -> null
      - private_dns_hostname_type_on_launch            = "ip-name" -> null
      - tags                                           = {
          - "Lab"  = "lab11"
          - "Name" = "lab11-app-a"
        } -> null
      - tags_all                                       = {
          - "Lab"  = "lab11"
          - "Name" = "lab11-app-a"
        } -> null
      - vpc_id                                         = "vpc-01817457dfb9c55ff" -> null
        # (4 unchanged attributes hidden)
    }

  # aws_vpc.main will be destroyed
  - resource "aws_vpc" "main" {
      - arn                                  = "arn:aws:ec2:us-east-2:027488552956:vpc/vpc-01817457dfb9c55ff" -> null
      - assign_generated_ipv6_cidr_block     = false -> null
      - cidr_block                           = "10.0.0.0/16" -> null
      - default_network_acl_id               = "acl-0083e2444329235ee" -> null
      - default_route_table_id               = "rtb-0fa7c5e1e4bc0c14a" -> null
      - default_security_group_id            = "sg-04fc1e4808d13c6b1" -> null
      - dhcp_options_id                      = "dopt-0b3fb1f3b525c8788" -> null
      - enable_dns_hostnames                 = false -> null
      - enable_dns_support                   = true -> null
      - enable_network_address_usage_metrics = false -> null
      - id                                   = "vpc-01817457dfb9c55ff" -> null
      - instance_tenancy                     = "default" -> null
      - ipv6_netmask_length                  = 0 -> null
      - main_route_table_id                  = "rtb-0fa7c5e1e4bc0c14a" -> null
      - owner_id                             = "027488552956" -> null
      - tags                                 = {
          - "Lab"  = "lab11"
          - "Name" = "lab11-collections"
        } -> null
      - tags_all                             = {
          - "Lab"  = "lab11"
          - "Name" = "lab11-collections"
        } -> null
        # (4 unchanged attributes hidden)
    }

  # terraform_data.collections will be destroyed
  - resource "terraform_data" "collections" {
      - id     = "d57e79e8-3f82-3807-d929-0f55773e1b5d" -> null
      - input  = {
          - list_index_1  = "api"
          - list_length   = 3
          - map_key_app_a = "10.0.1.0/24"
          - map_keys      = [
              - "app_a",
              - "app_b",
            ]
          - map_length    = 2
          - set_length    = 2
        } -> null
      - output = {
          - list_index_1  = "api"
          - list_length   = 3
          - map_key_app_a = "10.0.1.0/24"
          - map_keys      = [
              - "app_a",
              - "app_b",
            ]
          - map_length    = 2
          - set_length    = 2
        } -> null
    }

Plan: 0 to add, 0 to change, 3 to destroy.

Changes to Outputs:
  - app_a_subnet_from_map  = {
      - actual_az      = "us-east-2a"
      - actual_cidr    = "10.0.1.0/24"
      - requested_az   = "us-east-2a"
      - requested_cidr = "10.0.1.0/24"
    } -> null
  - app_a_subnet_id        = "subnet-01c25594879924dc0" -> null
  - collection_shapes      = {
      - list_index_1  = "api"
      - list_length   = 3
      - map_key_app_a = "10.0.1.0/24"
      - map_keys      = [
          - "app_a",
          - "app_b",
        ]
      - map_length    = 2
      - set_length    = 2
    } -> null
  - list_has_duplicates    = [
      - "web",
      - "api",
      - "web",
    ] -> null
  - set_removed_duplicates = [
      - "us-east-2a",
      - "us-east-2b",
    ] -> null
  - subnet_cidrs           = {
      - app_a = "10.0.1.0/24"
      - app_b = "10.0.2.0/24"
    } -> null
  - tag_labels             = [
      - "WEB",
      - "API",
      - "WEB",
    ] -> null
  - unique_tag_names       = [
      - "api",
      - "web",
    ] -> null
  - vpc_id                 = "vpc-01817457dfb9c55ff" -> null
  - zone_a_subnets         = [
      - "app_a",
    ] -> null
terraform_data.collections: Destroying... [id=d57e79e8-3f82-3807-d929-0f55773e1b5d]
terraform_data.collections: Destruction complete after 0s
aws_subnet.app_a: Destroying... [id=subnet-01c25594879924dc0]
aws_subnet.app_a: Destruction complete after 2s
aws_vpc.main: Destroying... [id=vpc-01817457dfb9c55ff]
aws_vpc.main: Destruction complete after 1s

Destroy complete! Resources: 3 destroyed.
```

`Destroy complete! Resources: 3 destroyed.` The subnet goes first, then the VPC that contained it,
because Terraform reverses the dependency order on destroy.

## Done when

- [ ] You can state the difference between list, set, and map in one sentence each
- [ ] `toset(["web","api","web"])` returned two elements, sorted
- [ ] `apply` reported `3 added` and printed ten outputs
- [ ] `set_removed_duplicates` shows two zones, not three
- [ ] The list `for` expression returned `["WEB","API","WEB"]` — three elements, order preserved
- [ ] The map `for` expression returned a map keyed `app_a` and `app_b`
- [ ] The `if` clause left only `app_a`
- [ ] `state show` reported `list_length = 3` beside `set_length = 2`
- [ ] `aws_subnet.app_a` exists in AWS with CIDR `10.0.1.0/24` in `us-east-2a`, neither value typed
      into the resource block
- [ ] Shortening the list moved `list_index_1`; shortening the map did not move `map_key_app_a`, and
      left the real subnet untouched
- [ ] You can say why this lab creates one subnet and not two
- [ ] `terraform destroy` reports `3 destroyed`

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
| `InvalidSubnet.Range: not a valid subnet of the VPC` | A `subnets` entry falls outside `vpc_cidr` | Keep every CIDR inside `10.0.0.0/16`, or raise `vpc_cidr` |
| `InvalidParameterValue: value for availability zone is invalid` | An `az` outside the region | `us-east-2` has only `us-east-2a`, `us-east-2b` and `us-east-2c` |
| `VpcLimitExceeded` | Five VPCs already exist in the region | Destroy a previous lab's VPC first |
| `NoCredentialProviders` or `InvalidClientTokenId` | Credentials missing or expired | Refresh them and confirm with `aws sts get-caller-identity` |

## Cleanup

```bash
terraform destroy -auto-approve
rm -rf .terraform terraform.tfstate*
```

## Next steps

- Deep dive: [docs/09-collections-functions.md](../docs/09-collections-functions.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab11-collections)
- Continue to [Lab 12 — Functions](lab12-functions.md)
