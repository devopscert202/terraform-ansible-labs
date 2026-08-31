# Lab 12 — Functions

| | |
|---|---|
| **Goal** | Transform values with Terraform's built-in functions inside a `locals` block, test an expression in `terraform console` before committing it to a file, and let the results define a real subnet and security group. |
| **Time** | 40–50 minutes |
| **Tier** | Intermediate |
| **Files** | `terraform/labs/lab12-functions/` |

## Overview

A **function** takes values in and returns a new value: `lower("ABC")` returns `"abc"`. Terraform
ships a fixed set of them and you cannot write your own, so learning the catalogue is the whole
skill. They group into families — string, collection, numeric, network, encoding, and a few
defensive ones — and you reach for them whenever a value needs reshaping between the input a human
types and the format AWS demands.

Functions cannot be called at the top level of a file. They live inside expressions, and the usual
home for a non-trivial expression is a `locals` block, which you met in Lab 06. The other tool this
lab leans on is `terraform console`, an interactive prompt where you evaluate an expression and
see the answer immediately instead of guessing and re-running `plan`. Labs 06 and 11 used it one
expression at a time; here you stay inside it. You will work through one family per step at that
prompt, then see the same functions used for real in the configuration.

"For real" is the part that matters. A function whose result is only printed teaches syntax and
nothing else. So the last third of this lab builds a VPC, a subnet whose CIDR is whatever
`cidrsubnet()` returned, and a security group whose ingress ranges are whatever
`sort(tolist(toset(...)))` returned. Nothing in the network is typed twice: change `var.vpc_cidr` and
the subnet moves, because the function recomputes it.

A VPC, a subnet and a security group cost nothing, but they are real, so this lab needs AWS
credentials.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `local.slug` | `lower()` and `replace()` turn a display name into a safe identifier | Free |
| `local.unique_cidrs` | `toset()`, `tolist()`, `sort()` deduplicate and order a list | Free |
| `local.cidr_count` | `length()` counts the result | Free |
| `local.subnet_prefix` | `cidrsubnet()` carves a subnet range out of `var.vpc_cidr` | Free |
| `local.config_json` | `jsonencode()` renders an object as a JSON string | Free |
| `local.summary` | `format()` builds a display string | Free |
| `aws_vpc.main` | The lab's own VPC, `10.20.0.0/16` | Free |
| `aws_subnet.derived` | A real subnet at the CIDR `cidrsubnet()` computed | Free |
| `aws_security_group.app` | Ingress ranges taken from `local.unique_cidrs` | Free |

Three managed resources, no data sources.

## Before you start

- [ ] Lab 11 completed ([lab11-collections.md](lab11-collections.md))
- [ ] You know what a list, a set, and a map are
- [ ] AWS credentials configured for `us-east-2` (`aws sts get-caller-identity` succeeds)
- [ ] Working directory: `../labs/lab12-functions/`

## Steps

### Step 1 — Read the locals block

```bash
cd terraform/labs/lab12-functions
cat main.tf
```

Every value is built by a function, and several nest one call inside another. Read nested calls
from the inside out: in `lower(replace(var.application, " ", "-"))` the `replace()` runs first and
its result becomes the argument to `lower()`.

### Step 2 — Open the console

```bash
terraform init
terraform console
```

**Expected output**

```text
>
```

The prompt is `>`. It evaluates one expression at a time and prints the result. Nothing you type here
changes any file or any infrastructure. Stay at this prompt for Steps 3 through 13.

### Step 3 — String functions: reshape text

```text
lower("Payments API")
replace("payments api", " ", "-")
```

**Expected output**

```text
"payments api"
"payments-api"
```

`lower()` folds the case. `replace()` swaps every occurrence of its second argument for the third.
Chained, they turn a human-written name into an identifier safe to use in a resource name — which
is exactly what `local.slug` does.

### Step 4 — String functions: uppercase and join

```text
upper("prod")
join(", ", ["web", "api", "db"])
```

**Expected output**

```text
"PROD"
"web, api, db"
```

`join()` collapses a list into one string with a separator between elements. It is the function you
want whenever a provider argument takes a comma-separated string but your data is a list.

### Step 5 — Collection functions: remove duplicates

```text
toset(["10.0.2.0/24","10.0.1.0/24","10.0.1.0/24"])
```

**Expected output**

```text
toset([
  "10.0.1.0/24",
  "10.0.2.0/24",
])
```

`toset()` converts a list to a set, and sets cannot hold duplicates, so the repeated CIDR is gone.
Three values in, two out. The `toset([...])` wrapper in the display is Terraform telling you the
result's type, not part of the value.

### Step 6 — Collection functions: get a stable order

```text
sort(tolist(toset(["10.0.2.0/24","10.0.1.0/24","10.0.1.0/24"])))
```

**Expected output**

```text
tolist([
  "10.0.1.0/24",
  "10.0.2.0/24",
])
```

A set has no defined order, so you cannot rely on how it prints. `tolist()` converts back to a list
and `sort()` puts it in a predictable order. This three-function chain is the standard idiom for
cleaning up a list of CIDRs, and it is what `local.unique_cidrs` uses.

### Step 7 — Numeric functions: count and compare

```text
length(["a","b","c"])
max(3, 9, 1)
min(3, 9, 1)
```

**Expected output**

```text
3
9
1
```

`length()` works on lists, sets, maps, and strings, which makes it the function you use to turn a
collection into the number that `count` requires — [Lab 24](lab24-count-foreach-buckets.md) does
exactly that against real S3 buckets.

### Step 8 — Network functions: carve out a subnet range

```text
cidrsubnet("10.20.0.0/16", 8, 12)
```

**Expected output**

```text
"10.20.12.0/24"
```

`cidrsubnet(prefix, newbits, netnum)` splits a range. Adding `8` bits to a `/16` gives `/24`
blocks, and `12` selects the thirteenth of them, counting from zero. Doing this arithmetic by hand
is a reliable source of outages, so let the function do it.

Remember this value. `10.20.12.0/24` is the CIDR of the real subnet you create in Step 16, and it is
never typed into the resource block.

### Step 9 — Network functions: pick a specific host address

```text
cidrhost("10.20.12.0/24", 5)
```

**Expected output**

```text
"10.20.12.5"
```

`cidrhost()` returns one address from inside a range. Use it when something needs a fixed IP that
must still move correctly if the surrounding CIDR changes.

### Step 10 — Encoding functions: produce JSON

```text
jsonencode({name = "payments-api", ports = [80, 443]})
```

**Expected output**

```text
"{\"name\":\"payments-api\",\"ports\":[80,443]}"
```

`jsonencode()` turns a Terraform object into a JSON *string*. The backslashes are escaped quotes,
because the result is a single string containing JSON, not an object. IAM policy documents and
user-data payloads both want this form.

### Step 11 — Formatting functions: build a display string

```text
format("%s uses %d CIDRs", "payments-api", 2)
```

**Expected output**

```text
"payments-api uses 2 CIDRs"
```

`format()` substitutes values into a template: `%s` for a string, `%d` for a number. Terraform has
no `printf`; this is it.

### Step 12 — Defensive functions: supply a fallback

```text
coalesce(null, "", "fallback")
try(tonumber("abc"), 0)
```

**Expected output**

```text
"fallback"
0
```

`coalesce()` returns its first argument that is neither null nor empty. `try()` evaluates its
arguments in order and returns the first that does not error — here `tonumber("abc")` fails, so the
fallback `0` is returned. These keep a configuration working when an optional input is absent.

### Step 13 — Evaluate this configuration's own values

```text
local.slug
local.unique_cidrs
local.summary
```

**Expected output**

```text
"payments-api"
tolist([
  "10.0.1.0/24",
  "10.0.2.0/24",
])
"payments-api uses 2 unique CIDR(s)"
```

The console loads the configuration in the current directory, so `var.*`, `local.*`, and — after an
apply — resource attributes are all available. You are now reading the same values you traced by
hand in Steps 3 through 11.

### Step 14 — Leave the console

```text
exit
```

You are back at your shell prompt. If an expression is wrong the console prints the error and stays
open, which makes it far cheaper than discovering the same mistake during an `apply`.

### Step 15 — Read where the function results are consumed

```bash
sed -n '/^# A VPC of its own/,$p' main.tf
```

**Expected output**

```text
# A VPC of its own, so the lab never depends on the account having a default VPC.
resource "aws_vpc" "main" {
  cidr_block         = var.vpc_cidr
  enable_dns_support = true

  tags = local.common_tags
}

# cidrsubnet() doing real work. The CIDR below was never typed by hand: it is
# computed from var.vpc_cidr, so this is the arithmetic the function replaced.
resource "aws_subnet" "derived" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = local.subnet_prefix
  availability_zone = var.subnet_az

  tags = merge(local.common_tags, { Name = "${local.slug}-derived" })
}

# The deduplicated, sorted CIDR list becomes the real source ranges of a real
# security group. There is no internet gateway, so nothing outside reaches this.
resource "aws_security_group" "app" {
  name        = "${local.slug}-sg"
  description = "Lab 12: ingress ranges built by toset(), tolist() and sort()"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTPS from the deduplicated CIDR list"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = local.unique_cidrs
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { Name = "${local.slug}-sg" })
}
```

Read what is *absent* from those blocks. No CIDR is written out for the subnet — `local.subnet_prefix`
supplies it. No ingress range is listed — `local.unique_cidrs` supplies them, already deduplicated
and sorted. No resource name is written — `local.slug` supplies it. Three function families, three
real arguments.

`local.config_json` is the exception: `jsonencode()` output is still only an output here, because its
real destination is an IAM policy document, which this track does not cover.

### Step 16 — Apply and read every result at once

```bash
terraform apply -auto-approve
```

**Expected output**

```text

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # aws_security_group.app will be created
  + resource "aws_security_group" "app" {
      + arn                    = (known after apply)
      + description            = "Lab 12: ingress ranges built by toset(), tolist() and sort()"
      + egress                 = [
          + {
              + cidr_blocks      = [
                  + "0.0.0.0/0",
                ]
              + description      = "All outbound"
              + from_port        = 0
              + ipv6_cidr_blocks = []
              + prefix_list_ids  = []
              + protocol         = "-1"
              + security_groups  = []
              + self             = false
              + to_port          = 0
            },
        ]
      + id                     = (known after apply)
      + ingress                = [
          + {
              + cidr_blocks      = [
                  + "10.0.1.0/24",
                  + "10.0.2.0/24",
                ]
              + description      = "HTTPS from the deduplicated CIDR list"
              + from_port        = 443
              + ipv6_cidr_blocks = []
              + prefix_list_ids  = []
              + protocol         = "tcp"
              + security_groups  = []
              + self             = false
              + to_port          = 443
            },
        ]
      + name                   = "payments-api-sg"
      + name_prefix            = (known after apply)
      + owner_id               = (known after apply)
      + revoke_rules_on_delete = false
      + tags                   = {
          + "Lab"     = "lab12"
          + "Name"    = "payments-api-sg"
          + "Summary" = "payments-api uses 2 unique CIDR(s)"
        }
      + tags_all               = {
          + "Lab"     = "lab12"
          + "Name"    = "payments-api-sg"
          + "Summary" = "payments-api uses 2 unique CIDR(s)"
        }
      + vpc_id                 = (known after apply)
    }

  # aws_subnet.derived will be created
  + resource "aws_subnet" "derived" {
      + arn                                            = (known after apply)
      + assign_ipv6_address_on_creation                = false
      + availability_zone                              = "us-east-2a"
      + availability_zone_id                           = (known after apply)
      + cidr_block                                     = "10.20.12.0/24"
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
          + "Lab"     = "lab12"
          + "Name"    = "payments-api-derived"
          + "Summary" = "payments-api uses 2 unique CIDR(s)"
        }
      + tags_all                                       = {
          + "Lab"     = "lab12"
          + "Name"    = "payments-api-derived"
          + "Summary" = "payments-api uses 2 unique CIDR(s)"
        }
      + vpc_id                                         = (known after apply)
    }

  # aws_vpc.main will be created
  + resource "aws_vpc" "main" {
      + arn                                  = (known after apply)
      + cidr_block                           = "10.20.0.0/16"
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
          + "Lab"     = "lab12"
          + "Name"    = "payments-api"
          + "Summary" = "payments-api uses 2 unique CIDR(s)"
        }
      + tags_all                             = {
          + "Lab"     = "lab12"
          + "Name"    = "payments-api"
          + "Summary" = "payments-api uses 2 unique CIDR(s)"
        }
    }

Plan: 3 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + cidr_count                   = 2
  + config_json                  = jsonencode(
        {
          + cidrs = [
              + "10.0.1.0/24",
              + "10.0.2.0/24",
            ]
          + name  = "payments-api"
        }
    )
  + derived_subnet               = {
      + assigned_by_aws        = "10.20.12.0/24"
      + computed_by_cidrsubnet = "10.20.12.0/24"
      + subnet_id              = (known after apply)
    }
  + derived_subnet_gateway_host  = "10.20.12.1"
  + security_group_ingress_cidrs = [
      + "10.0.1.0/24",
      + "10.0.2.0/24",
    ]
  + slug                         = "payments-api"
  + subnet_prefix                = "10.20.12.0/24"
  + summary                      = "payments-api uses 2 unique CIDR(s)"
  + unique_cidrs                 = [
      + "10.0.1.0/24",
      + "10.0.2.0/24",
    ]
  + vpc_id                       = (known after apply)
aws_vpc.main: Creating...
aws_vpc.main: Creation complete after 6s [id=vpc-02fb7b6743ecd2656]
aws_subnet.derived: Creating...
aws_security_group.app: Creating...
aws_subnet.derived: Creation complete after 2s [id=subnet-003a9ca6d15ebc66b]
aws_security_group.app: Creation complete after 4s [id=sg-06781f7b1cd1c6ddf]

Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

Outputs:

cidr_count = 2
config_json = "{\"cidrs\":[\"10.0.1.0/24\",\"10.0.2.0/24\"],\"name\":\"payments-api\"}"
derived_subnet = {
  "assigned_by_aws" = "10.20.12.0/24"
  "computed_by_cidrsubnet" = "10.20.12.0/24"
  "subnet_id" = "subnet-003a9ca6d15ebc66b"
}
derived_subnet_gateway_host = "10.20.12.1"
security_group_ingress_cidrs = tolist([
  "10.0.1.0/24",
  "10.0.2.0/24",
])
slug = "payments-api"
subnet_prefix = "10.20.12.0/24"
summary = "payments-api uses 2 unique CIDR(s)"
unique_cidrs = tolist([
  "10.0.1.0/24",
  "10.0.2.0/24",
])
vpc_id = "vpc-02fb7b6743ecd2656"
```

`Plan: 3 to add, 0 to change, 0 to destroy.` Check `derived_subnet` in the outputs:
`computed_by_cidrsubnet` and `assigned_by_aws` are both `10.20.12.0/24`. The first is what the
function returned; the second is what AWS recorded. They match, which is the whole point.

`security_group_ingress_cidrs` reads the ranges back off the real security group and shows two, not
three — `toset()` removed the duplicate before it ever left your machine.

### Step 17 — Confirm the derived values in state

```bash
terraform state show aws_subnet.derived
terraform output derived_subnet_gateway_host
```

**Expected output**

```text
# aws_subnet.derived:
resource "aws_subnet" "derived" {
    arn                                            = "arn:aws:ec2:us-east-2:027488552956:subnet/subnet-003a9ca6d15ebc66b"
    assign_ipv6_address_on_creation                = false
    availability_zone                              = "us-east-2a"
    availability_zone_id                           = "use2-az1"
    cidr_block                                     = "10.20.12.0/24"
    customer_owned_ipv4_pool                       = null
    enable_dns64                                   = false
    enable_lni_at_device_index                     = 0
    enable_resource_name_dns_a_record_on_launch    = false
    enable_resource_name_dns_aaaa_record_on_launch = false
    id                                             = "subnet-003a9ca6d15ebc66b"
    ipv6_cidr_block                                = null
    ipv6_cidr_block_association_id                 = null
    ipv6_native                                    = false
    map_customer_owned_ip_on_launch                = false
    map_public_ip_on_launch                        = false
    outpost_arn                                    = null
    owner_id                                       = "027488552956"
    private_dns_hostname_type_on_launch            = "ip-name"
    tags                                           = {
        "Lab"     = "lab12"
        "Name"    = "payments-api-derived"
        "Summary" = "payments-api uses 2 unique CIDR(s)"
    }
    tags_all                                       = {
        "Lab"     = "lab12"
        "Name"    = "payments-api-derived"
        "Summary" = "payments-api uses 2 unique CIDR(s)"
    }
    vpc_id                                         = "vpc-02fb7b6743ecd2656"
}
"10.20.12.1"
```

`cidr_block` is `10.20.12.0/24` and `derived_subnet_gateway_host` is `10.20.12.1` — `cidrhost()`
applied to a CIDR that came back from AWS rather than one you typed.

### Step 18 — Move the VPC and watch the subnet follow

The subnet's CIDR is derived from the VPC's, so changing one input should move both. Nothing is
applied here — `plan` only reports.

```bash
terraform plan -var 'vpc_cidr=10.30.0.0/16'
```

**Expected output**

```text
aws_vpc.main: Refreshing state... [id=vpc-02fb7b6743ecd2656]
aws_subnet.derived: Refreshing state... [id=subnet-003a9ca6d15ebc66b]
aws_security_group.app: Refreshing state... [id=sg-06781f7b1cd1c6ddf]

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
-/+ destroy and then create replacement

Terraform will perform the following actions:

  # aws_security_group.app must be replaced
-/+ resource "aws_security_group" "app" {
      ~ arn                    = "arn:aws:ec2:us-east-2:027488552956:security-group/sg-06781f7b1cd1c6ddf" -> (known after apply)
      ~ id                     = "sg-06781f7b1cd1c6ddf" -> (known after apply)
        name                   = "payments-api-sg"
      + name_prefix            = (known after apply)
      ~ owner_id               = "027488552956" -> (known after apply)
        tags                   = {
            "Lab"     = "lab12"
            "Name"    = "payments-api-sg"
            "Summary" = "payments-api uses 2 unique CIDR(s)"
        }
      ~ vpc_id                 = "vpc-02fb7b6743ecd2656" -> (known after apply) # forces replacement
        # (5 unchanged attributes hidden)
    }

  # aws_subnet.derived must be replaced
-/+ resource "aws_subnet" "derived" {
      ~ arn                                            = "arn:aws:ec2:us-east-2:027488552956:subnet/subnet-003a9ca6d15ebc66b" -> (known after apply)
      ~ availability_zone_id                           = "use2-az1" -> (known after apply)
      ~ cidr_block                                     = "10.20.12.0/24" -> "10.30.12.0/24" # forces replacement
      - enable_lni_at_device_index                     = 0 -> null
      ~ id                                             = "subnet-003a9ca6d15ebc66b" -> (known after apply)
      + ipv6_cidr_block_association_id                 = (known after apply)
      - map_customer_owned_ip_on_launch                = false -> null
      ~ owner_id                                       = "027488552956" -> (known after apply)
      ~ private_dns_hostname_type_on_launch            = "ip-name" -> (known after apply)
        tags                                           = {
            "Lab"     = "lab12"
            "Name"    = "payments-api-derived"
            "Summary" = "payments-api uses 2 unique CIDR(s)"
        }
      ~ vpc_id                                         = "vpc-02fb7b6743ecd2656" -> (known after apply) # forces replacement
        # (11 unchanged attributes hidden)
    }

  # aws_vpc.main must be replaced
-/+ resource "aws_vpc" "main" {
      ~ arn                                  = "arn:aws:ec2:us-east-2:027488552956:vpc/vpc-02fb7b6743ecd2656" -> (known after apply)
      - assign_generated_ipv6_cidr_block     = false -> null
      ~ cidr_block                           = "10.20.0.0/16" -> "10.30.0.0/16" # forces replacement
      ~ default_network_acl_id               = "acl-0578a059306a17ef5" -> (known after apply)
      ~ default_route_table_id               = "rtb-065c8b333df48c9c1" -> (known after apply)
      ~ default_security_group_id            = "sg-042d2ccb98d9aec3a" -> (known after apply)
      ~ dhcp_options_id                      = "dopt-0b3fb1f3b525c8788" -> (known after apply)
      ~ enable_dns_hostnames                 = false -> (known after apply)
      ~ enable_network_address_usage_metrics = false -> (known after apply)
      ~ id                                   = "vpc-02fb7b6743ecd2656" -> (known after apply)
      + ipv6_association_id                  = (known after apply)
      + ipv6_cidr_block                      = (known after apply)
      + ipv6_cidr_block_network_border_group = (known after apply)
      - ipv6_netmask_length                  = 0 -> null
      ~ main_route_table_id                  = "rtb-065c8b333df48c9c1" -> (known after apply)
      ~ owner_id                             = "027488552956" -> (known after apply)
        tags                                 = {
            "Lab"     = "lab12"
            "Name"    = "payments-api"
            "Summary" = "payments-api uses 2 unique CIDR(s)"
        }
        # (4 unchanged attributes hidden)
    }

Plan: 3 to add, 0 to change, 3 to destroy.

Changes to Outputs:
  ~ derived_subnet               = {
      ~ assigned_by_aws        = "10.20.12.0/24" -> "10.30.12.0/24"
      ~ computed_by_cidrsubnet = "10.20.12.0/24" -> "10.30.12.0/24"
      ~ subnet_id              = "subnet-003a9ca6d15ebc66b" -> (known after apply)
    }
  ~ derived_subnet_gateway_host  = "10.20.12.1" -> "10.30.12.1"
  ~ subnet_prefix                = "10.20.12.0/24" -> "10.30.12.0/24"
  ~ vpc_id                       = "vpc-02fb7b6743ecd2656" -> (known after apply)

─────────────────────────────────────────────────────────────────────────────

Note: You didn't use the -out option to save this plan, so Terraform can't
guarantee to take exactly these actions if you run "terraform apply" now.
```

Terraform proposes replacing all three resources: the VPC because `cidr_block` cannot be changed in place,
the subnet because `cidrsubnet("10.30.0.0/16", 8, 12)` is now `10.30.12.0/24`, and the security group
because its `vpc_id` is being replaced underneath it. `Plan: 3 to add, 0 to change, 3 to destroy.` —
one edit, three correct consequences. Had the subnet CIDR been hardcoded, the same edit would have produced a subnet
outside its own VPC and an `InvalidSubnet.Range` error at apply.

### Step 19 — Change an input and watch every derived value follow

```bash
terraform plan -var 'application=Billing Service'
```

**Expected output**

```text
aws_vpc.main: Refreshing state... [id=vpc-02fb7b6743ecd2656]
aws_subnet.derived: Refreshing state... [id=subnet-003a9ca6d15ebc66b]
aws_security_group.app: Refreshing state... [id=sg-06781f7b1cd1c6ddf]

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  ~ update in-place
-/+ destroy and then create replacement

Terraform will perform the following actions:

  # aws_security_group.app must be replaced
-/+ resource "aws_security_group" "app" {
      ~ arn                    = "arn:aws:ec2:us-east-2:027488552956:security-group/sg-06781f7b1cd1c6ddf" -> (known after apply)
      ~ id                     = "sg-06781f7b1cd1c6ddf" -> (known after apply)
      ~ name                   = "payments-api-sg" -> "billing-service-sg" # forces replacement
      + name_prefix            = (known after apply)
      ~ owner_id               = "027488552956" -> (known after apply)
      ~ tags                   = {
            "Lab"     = "lab12"
          ~ "Name"    = "payments-api-sg" -> "billing-service-sg"
          ~ "Summary" = "payments-api uses 2 unique CIDR(s)" -> "billing-service uses 2 unique CIDR(s)"
        }
      ~ tags_all               = {
          ~ "Name"    = "payments-api-sg" -> "billing-service-sg"
          ~ "Summary" = "payments-api uses 2 unique CIDR(s)" -> "billing-service uses 2 unique CIDR(s)"
            # (1 unchanged element hidden)
        }
        # (5 unchanged attributes hidden)
    }

  # aws_subnet.derived will be updated in-place
  ~ resource "aws_subnet" "derived" {
        id                                             = "subnet-003a9ca6d15ebc66b"
      ~ tags                                           = {
            "Lab"     = "lab12"
          ~ "Name"    = "payments-api-derived" -> "billing-service-derived"
          ~ "Summary" = "payments-api uses 2 unique CIDR(s)" -> "billing-service uses 2 unique CIDR(s)"
        }
      ~ tags_all                                       = {
          ~ "Name"    = "payments-api-derived" -> "billing-service-derived"
          ~ "Summary" = "payments-api uses 2 unique CIDR(s)" -> "billing-service uses 2 unique CIDR(s)"
            # (1 unchanged element hidden)
        }
        # (19 unchanged attributes hidden)
    }

  # aws_vpc.main will be updated in-place
  ~ resource "aws_vpc" "main" {
        id                                   = "vpc-02fb7b6743ecd2656"
      ~ tags                                 = {
            "Lab"     = "lab12"
          ~ "Name"    = "payments-api" -> "billing-service"
          ~ "Summary" = "payments-api uses 2 unique CIDR(s)" -> "billing-service uses 2 unique CIDR(s)"
        }
      ~ tags_all                             = {
          ~ "Name"    = "payments-api" -> "billing-service"
          ~ "Summary" = "payments-api uses 2 unique CIDR(s)" -> "billing-service uses 2 unique CIDR(s)"
            # (1 unchanged element hidden)
        }
        # (18 unchanged attributes hidden)
    }

Plan: 1 to add, 2 to change, 1 to destroy.

Changes to Outputs:
  ~ config_json                  = jsonencode(
      ~ {
          ~ name  = "payments-api" -> "billing-service"
            # (1 unchanged attribute hidden)
        }
    )
  ~ slug                         = "payments-api" -> "billing-service"
  ~ summary                      = "payments-api uses 2 unique CIDR(s)" -> "billing-service uses 2 unique CIDR(s)"

─────────────────────────────────────────────────────────────────────────────

Note: You didn't use the -out option to save this plan, so Terraform can't
guarantee to take exactly these actions if you run "terraform apply" now.
```

`slug`, `summary` and `config_json` all change, and the security group is proposed for replacement
because its `name` is built from `local.slug`. One input changed and every value derived from it
followed, because each is computed rather than typed out. That is the reason to push transformation
into functions instead of hand-writing both forms.

### Step 20 — Destroy

```bash
terraform destroy -auto-approve
```

**Expected output**

```text
aws_vpc.main: Refreshing state... [id=vpc-02fb7b6743ecd2656]
aws_subnet.derived: Refreshing state... [id=subnet-003a9ca6d15ebc66b]
aws_security_group.app: Refreshing state... [id=sg-06781f7b1cd1c6ddf]

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  - destroy

Terraform will perform the following actions:

  # aws_security_group.app will be destroyed
  - resource "aws_security_group" "app" {
      - arn                    = "arn:aws:ec2:us-east-2:027488552956:security-group/sg-06781f7b1cd1c6ddf" -> null
      - description            = "Lab 12: ingress ranges built by toset(), tolist() and sort()" -> null

[... the full attribute listing for aws_security_group.app, aws_subnet.derived and aws_vpc.main is elided here ...]

Plan: 0 to add, 0 to change, 3 to destroy.

Changes to Outputs:
  - cidr_count                   = 2 -> null
  - config_json                  = jsonencode(
        {
          - cidrs = [
              - "10.0.1.0/24",
              - "10.0.2.0/24",
            ]
          - name  = "payments-api"
        }
    ) -> null
  - derived_subnet               = {
      - assigned_by_aws        = "10.20.12.0/24"
      - computed_by_cidrsubnet = "10.20.12.0/24"
      - subnet_id              = "subnet-003a9ca6d15ebc66b"
    } -> null
  - derived_subnet_gateway_host  = "10.20.12.1" -> null
  - security_group_ingress_cidrs = [
      - "10.0.1.0/24",
      - "10.0.2.0/24",
    ] -> null
  - slug                         = "payments-api" -> null
  - subnet_prefix                = "10.20.12.0/24" -> null
  - summary                      = "payments-api uses 2 unique CIDR(s)" -> null
  - unique_cidrs                 = [
      - "10.0.1.0/24",
      - "10.0.2.0/24",
    ] -> null
  - vpc_id                       = "vpc-02fb7b6743ecd2656" -> null
aws_subnet.derived: Destroying... [id=subnet-003a9ca6d15ebc66b]
aws_security_group.app: Destroying... [id=sg-06781f7b1cd1c6ddf]
aws_subnet.derived: Destruction complete after 1s
aws_security_group.app: Destruction complete after 1s
aws_vpc.main: Destroying... [id=vpc-02fb7b6743ecd2656]
aws_vpc.main: Destruction complete after 0s

Destroy complete! Resources: 3 destroyed.
```

`Destroy complete! Resources: 3 destroyed.`

## Done when

- [ ] `terraform console` opens and you evaluated an expression from every family above
- [ ] You produced `"payments-api"` with `lower()` and `replace()`
- [ ] `toset()` reduced three CIDRs to two, and `sort(tolist(...))` ordered them
- [ ] `cidrsubnet("10.20.0.0/16", 8, 12)` returned `"10.20.12.0/24"`
- [ ] `apply` reported `3 added`
- [ ] `derived_subnet` shows `computed_by_cidrsubnet` equal to `assigned_by_aws`
- [ ] `security_group_ingress_cidrs` lists two ranges, not three
- [ ] Overriding `vpc_cidr` moved the subnet's CIDR without you editing the subnet
- [ ] Overriding `application` changed `slug`, `summary`, and `config_json` together
- [ ] `terraform destroy` reports `3 destroyed`

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `Call to unknown function` | Misspelled name, or a function from another language | Terraform has no `printf`; use `format()` |
| `Invalid function argument` | Wrong type passed in | `sort()` needs a list; wrap a set in `tolist()` |
| `Invalid index` on `cidrsubnet` | `netnum` too large for the given `newbits` | `newbits = 8` allows `netnum` `0`–`255` |
| `Invalid value for "v" parameter` on `cidrhost` | Host number outside the range | Keep it below the range's host count |
| Console shows `(known after apply)` | Value depends on a resource not yet created | Run `apply` first, then reopen the console |
| Console will not exit | Waiting on an unclosed bracket or quote | Close it, or press `Ctrl-C` then type `exit` |
| `Variables not allowed` | Function or `var.` used at the top level of a file | Move the expression inside a `locals` block |
| `InvalidSubnet.Range: not a valid subnet of the VPC` | `subnet_newbits`/`subnet_netnum` selected a block outside `vpc_cidr` | Keep `newbits` at `8` and `netnum` in `0`–`255` for a `/16` |
| `InvalidParameterValue: value for availability zone is invalid` | `subnet_az` outside the region | `us-east-2` has only `us-east-2a`, `us-east-2b` and `us-east-2c` |
| `VpcLimitExceeded` | Five VPCs already exist in the region | Destroy a previous lab's VPC first |
| `NoCredentialProviders` or `InvalidClientTokenId` | Credentials missing or expired | Refresh them and confirm with `aws sts get-caller-identity` |

## Cleanup

```bash
terraform destroy -auto-approve
```

## Next steps

- Deep dive: [docs/09-collections-functions.md](../docs/09-collections-functions.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab12-functions)
- Continue to [Lab 13 — Multi-provider configuration](lab13-multi-provider.md)
