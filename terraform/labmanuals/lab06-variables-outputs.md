# Lab 06 — Variables and Outputs

| | |
|---|---|
| **Goal** | Declare a variable in every type HCL offers — primitive, collection, structural, nested, `any` — constrain them with `validation`, `nullable`, and `sensitive`, then read the results back through outputs and `terraform console`. |
| **Time** | 60–75 minutes |
| **Tier** | Intermediate |
| **Files** | `terraform/labs/lab06-variables-outputs/` |

## Overview

So far every value you wrote was fixed in the file. Change the region and you edit the file. A
**variable** is a named input you declare once and pass a value to from outside, so one configuration
can serve dev, test, and prod. An **output** is a named value Terraform prints after `apply` so you
can read an ID or IP address without hunting through the AWS console. A **local** is a value the
configuration works out for itself; nobody outside can set it.

Every variable also has a **type**, and the type is not decoration. It is a contract Terraform
enforces before it contacts AWS: pass a word where a number belongs and the run stops with an error
naming the variable, the line, and the type it wanted. This lab walks the whole HCL type system —
`string`, `number`, `bool`, `list`, `set`, `map`, `object`, `tuple`, the nested combinations of
those, and `any` — declaring one variable of each, then proving its behaviour with `terraform
console` and with deliberate failures.

Almost all of that happens without creating anything: the type lessons run against variables, locals,
and outputs, which cost nothing and answer in under a second. The lab does then build real
infrastructure so you can watch variables reach AWS — a small private network of one VPC, one subnet,
and one security group, with a single `t3.micro` instance inside it. That instance is deliberately
not reachable from the internet; Lab 21 is where a public instance gets built.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `data.aws_ami.al2023` | Looks up the newest Amazon Linux 2023 image | Free |
| `aws_vpc.main` | A private network of its own, `10.0.0.0/16` | Free |
| `aws_subnet.main` | One subnet, `10.0.1.0/24` in `us-east-2a`, where the instance launches | Free |
| `aws_security_group.instance` | Allows port 22 from inside the VPC only; all outbound | Free |
| `aws_instance.web` | One `t3.micro` instance in that subnet, tagged from a local | Free tier, otherwise a few cents/hour |
| 5 primitive variables | `aws_region`, `server_name`, `instance_type`, `root_volume_gb`, `enable_detailed_monitoring` | — |
| 3 collection variables | `role_list`, `role_set`, `tags` | — |
| 2 structural variables | `server_profile` (object with `optional()`), `release_marker` (tuple) | — |
| 2 nested variables | `disks` (`list(object)`), `environments` (`map(object)`) | — |
| 3 special variables | `freeform` (`any`), `owner_email` (`null` default), `api_token` (`sensitive`) | — |
| 3 network variables | `vpc_cidr`, `subnet_cidr`, `subnet_az` | — |
| 2 validation rules | One on a primitive, one on a `list(object)` | — |
| 5 locals | `common_tags`, `contact`, `owner_email_state`, `total_disk_gb`, `list_vs_set` | — |
| 15 outputs | Instance attributes, the three network IDs, plus one per type lesson | — |

## Before you start

- [ ] Lab 05 completed ([lab05-fmt-validate.md](lab05-fmt-validate.md))
- [ ] AWS credentials exported and `aws sts get-caller-identity` succeeds
- [ ] Working directory: `../labs/lab06-variables-outputs/`

## Steps

### Step 1 — Initialize

```bash
cd terraform/labs/lab06-variables-outputs
terraform init
```

**Expected output**

```text
Terraform has been successfully initialized!
```

`terraform console`, used throughout this lab, needs the provider installed, so `init` comes first.

### Step 2 — Read the primitive variables

The three primitive types are `string` (text), `number`, and `bool` (`true` or `false`).

```bash
sed -n '/variable "aws_region"/,/^}/p;/variable "root_volume_gb"/,/^}/p;/variable "enable_detailed_monitoring"/,/^}/p' variables.tf
```

**Expected output**

```text
variable "aws_region" {
  type        = string
  description = "AWS region the instance is created in."
  default     = "us-east-2"
}
variable "root_volume_gb" {
  type        = number
  description = "Root disk size in gibibytes. A number, so arithmetic works on it."
  default     = 8
}
variable "enable_detailed_monitoring" {
  type        = bool
  description = "Whether to turn on per-minute CloudWatch metrics. Bools accept only true or false."
  default     = false
}
```

Every `variable` block in this track has a name, a `type`, and a `description`. `default` is
optional — a variable without one is mandatory, and Terraform refuses to run until you supply a
value. The choice between `string` and `number` is not cosmetic: `root_volume_gb` is added to other
sizes in a local, and arithmetic on text is what the next step is about.

### Step 3 — Watch Terraform convert between primitives

```bash
echo 'tostring(42)' | terraform console
echo 'tonumber("8")' | terraform console
echo 'tobool("true")' | terraform console
echo '"8" + 1' | terraform console
```

**Expected output**

```text
"42"
8
true
9
```

Terraform converts automatically between the three primitives whenever the conversion is
unambiguous, which is why `"8" + 1` is `9` rather than an error. A `number` variable therefore
accepts the string `"16"` from a tfvars file and stores `16`.

Now ask for a conversion that cannot succeed:

```bash
echo 'tonumber("abc")' | terraform console
```

**Expected output**

```text
Error: Invalid function argument

  on <console-input> line 1:
  (source code not available)

Invalid value for "v" parameter: cannot convert "abc" to number; given string
must be a decimal representation of a number.
```

The rule is that Terraform converts when exactly one interpretation exists and refuses when none
does. It never guesses.

### Step 4 — Trigger a type mismatch on a real variable

```bash
terraform plan -var 'root_volume_gb=large'
```

**Expected output**

```text
Error: Invalid value for input variable

  on variables.tf line 29:
  29: variable "root_volume_gb" {

Unsuitable value for var.root_volume_gb set using -var="root_volume_gb=...":
a number is required.
```

This is the error a type mismatch produces, and it is worth recognising on sight: `Invalid value for
input variable`, the declaring line, and the type that was wanted. The same shape appears for a
bool:

```bash
terraform plan -var 'enable_detailed_monitoring=maybe'
```

**Expected output**

```text
Error: Invalid value for input variable

  on variables.tf line 35:
  35: variable "enable_detailed_monitoring" {

Unsuitable value for var.enable_detailed_monitoring set using
-var="enable_detailed_monitoring=...": a bool is required.
```

Nothing reached AWS in either case. Type checking happens before any provider call.

### Step 5 — Read the collection variables

A collection holds many values of **one** element type. HCL has three, and the difference between
them is behaviour, not storage.

```bash
sed -n '/variable "role_list"/,/^}/p;/variable "role_set"/,/^}/p;/variable "tags"/,/^}/p' variables.tf
```

**Expected output**

```text
variable "role_list" {
  type        = list(string)
  description = "A list: ordered, duplicates kept, addressed by position. Note the repeated web."
  default     = ["web", "api", "web"]
}
variable "role_set" {
  type        = set(string)
  description = "A set: unordered, duplicates discarded. Same default as role_list, different result."
  default     = ["web", "api", "web"]
}
variable "tags" {
  type        = map(string)
  description = "A map: values addressed by string key. Merged into every resource tag set."
  default = {
    Environment = "training"
    Owner       = "platform-team"
  }
}
```

`role_list` and `role_set` have byte-for-byte identical defaults. Only the declared type differs.

### Step 6 — Prove that swapping list for set changes the result

```bash
echo 'var.role_list' | terraform console
echo 'var.role_set' | terraform console
```

**Expected output**

```text
tolist([
  "web",
  "api",
  "web",
])
toset([
  "api",
  "web",
])
```

Three values in, two out. The set discarded the duplicate `web`, and it reordered what remained —
`api` now prints first, because a set has no positions to preserve. That has a direct consequence:

```bash
echo 'var.role_list[0]' | terraform console
echo 'length(var.role_list)' | terraform console
echo 'length(var.role_set)' | terraform console
```

**Expected output**

```text
"web"
3
2
```

A list can be indexed by number. A set cannot be indexed at all — there is no first element to ask
for — so you convert it with `tolist()` first, and even then the order you get is sorted, not the
order you typed. Choose a `list` when order or repetition carries meaning, a `set` when the values
are a membership question ("which zones?"), and a `map` when each value needs a name you look it up
by. Lab 11 shows what this costs operationally, when `for_each` over a set behaves differently from
`count` over a list.

### Step 7 — Read the structural variables

Structural types hold values of **different** types together. An `object` names each attribute; a
`tuple` numbers them.

```bash
sed -n '/variable "server_profile"/,/^}/p' variables.tf
```

**Expected output**

```text
variable "server_profile" {
  type = object({
    name       = string
    cpu_count  = number
    public     = bool
    department = optional(string, "unassigned")
    extra_tags = optional(map(string), {})
  })
  description = "One object with named attributes of different types. optional() attributes may be omitted."
  default = {
    name      = "lab06-web"
    cpu_count = 2
    public    = true
  }
}
```

`name`, `cpu_count`, and `public` are required: every value assigned to this variable must supply all
three. `department` and `extra_tags` are wrapped in `optional()` with a fallback, so a caller may
leave them out. This is the everyday reason objects are usable at all — without `optional()`, adding
one attribute to a module's input object breaks every caller.

### Step 8 — See the optional attributes filled in

```bash
echo 'var.server_profile' | terraform console
```

**Expected output**

```text
{
  "cpu_count" = 2
  "department" = "unassigned"
  "extra_tags" = tomap({})
  "name" = "lab06-web"
  "public" = true
}
```

The default set three attributes and five came back. Terraform inserted the `optional()` fallbacks
during type conversion, so the rest of the configuration never has to test whether an attribute
exists.

### Step 9 — Read a tuple

```bash
echo 'var.release_marker' | terraform console
echo 'type(var.release_marker)' | terraform console
echo 'var.release_marker[1]' | terraform console
```

**Expected output**

```text
[
  "al2023",
  3,
  true,
]
tuple([
    string,
    number,
    bool,
])
3
```

A tuple is a fixed-length sequence where each position has its own type: position 0 is a string,
position 1 a number, position 2 a bool. `var.release_marker[1]` is still a number, not the string
`"3"`. Reach for a tuple rarely — an object with names is almost always clearer than remembering
that position 1 is the build number.

### Step 10 — Break the object and the tuple

```bash
terraform plan -var 'server_profile={name="x",cpu_count=2}'
```

**Expected output**

```text
Error: Invalid value for input variable

  on variables.tf line 70:
  70: variable "server_profile" {

Unsuitable value for var.server_profile set using -var="server_profile=...":
attribute "public" is required.
```

Terraform names the missing attribute. Omitting `department` instead produces no error at all,
because it is `optional()`.

```bash
terraform plan -var 'release_marker=["al2023",3]'
```

**Expected output**

```text
Error: Invalid value for input variable

  on variables.tf line 86:
  86: variable "release_marker" {

Unsuitable value for var.release_marker set using -var="release_marker=...":
tuple required.
```

Two elements where three were declared is not a shorter tuple; it is the wrong type.

### Step 11 — Read the nested types

Real configurations rarely use a bare `list(string)`. They use a collection whose elements are
objects.

```bash
sed -n '/variable "disks"/,/^  ]$/p;/variable "environments"/,/^}/p' variables.tf
```

**Expected output**

```text
variable "disks" {
  type = list(object({
    device  = string
    size_gb = number
  }))
  description = "A list of objects. Order matters and entries need no unique name."
  default = [
    { device = "/dev/sdb", size_gb = 10 },
    { device = "/dev/sdc", size_gb = 20 },
  ]
variable "environments" {
  type = map(object({
    instance_type = string
    replicas      = number
  }))
  description = "A map of objects. Each entry is addressed by its key rather than its position."
  default = {
    dev  = { instance_type = "t3.micro", replicas = 1 }
    prod = { instance_type = "t3.small", replicas = 3 }
  }
}
```

Use `list(object(...))` when the entries have no natural name and their order is meaningful. Use
`map(object(...))` when each entry has an identity — an environment, a subnet name, a region — that
you want to address directly and that should survive its neighbours being deleted.

### Step 12 — Reach into a nested value

```bash
echo 'var.environments' | terraform console
echo 'var.environments["prod"].instance_type' | terraform console
```

**Expected output**

```text
tomap({
  "dev" = {
    "instance_type" = "t3.micro"
    "replicas" = 1
  }
  "prod" = {
    "instance_type" = "t3.small"
    "replicas" = 3
  }
})
"t3.small"
```

`["prod"]` selects the map entry, then `.instance_type` selects an attribute of the object stored
there. Terraform knows the type at every step, so a typo in the attribute name fails immediately
rather than producing an empty value.

### Step 13 — Look at `any`, and why to avoid it

```bash
echo 'var.freeform' | terraform console
echo 'type(var.freeform)' | terraform console
```

**Expected output**

```text
{
  "count" = 1
  "note" = "any switches type checking off"
}
object({
    count: number,
    note: string,
})
```

`type = any` accepts whatever it is given. Terraform infers a type from the value it happens to
receive, which is what the second command shows — nothing here was declared. Every guarantee from
Steps 4 and 10 is gone: a caller can pass a string tomorrow and the failure surfaces deep inside your
configuration, pointing at the line that used the value rather than the line that supplied it. Use
`any` only when the shape genuinely cannot be known, and prefer a real type everywhere else.

### Step 14 — Tell `null` apart from an empty string

`null` means "no value". It is not `""`, and it is not the same as leaving a variable out.

```bash
echo 'var.owner_email' | terraform console
terraform plan | grep -E 'owner_email_state|contact'
```

**Expected output**

```text
tostring(null)
  + contact            = "unset@example.invalid"
  + owner_email_state  = "null: no value was supplied"
```

`owner_email` declares `default = null`, so the console prints `tostring(null)` — a null of string
type. Now set it to an empty string instead:

```bash
terraform plan -var 'owner_email=' | grep -E 'owner_email_state|contact'
```

**Expected output**

```text
  + contact            = "unset@example.invalid"
  + owner_email_state  = "empty string: a value was supplied and it is blank"
```

The two cases are distinguishable — `local.owner_email_state` tests `== null` and `== ""` separately
— but `local.contact` is the same either way, because `coalesce()` skips both nulls and empty
strings. Assigning `null` to a resource argument is also how you say "leave this unset and let the
provider default apply", which is different from assigning `""`.

### Step 15 — See what `nullable = false` actually does

`instance_type` is declared `nullable = false`.

```bash
echo 'instance_type = null' > /tmp/null-test.tfvars
terraform plan -var-file=/tmp/null-test.tfvars | grep 'instance_type  '
```

**Expected output**

```text
      + instance_type                        = "t3.micro"
```

No error, and the instance still gets `t3.micro`. `nullable = false` does not reject null; it
guarantees the variable is never null inside the configuration, by substituting the `default` when
null is supplied. If such a variable had no `default`, the same input would be an error instead.
Delete the scratch file when you are done: `rm /tmp/null-test.tfvars`.

### Step 16 — Confirm `sensitive = true` redacts the value

```bash
echo 'var.api_token' | terraform console
```

**Expected output**

```text
(sensitive value)
```

The variable holds a placeholder string, and Terraform will not print it — not in the console, not in
a plan, not in an apply. Any output derived from it must also be marked `sensitive = true` or
`validate` refuses the configuration. `sensitive` suppresses display only; it is neither encryption
nor access control, and Lab 07 shows the value sitting in clear text in the state file.

### Step 17 — Trip the validation rule on a primitive

A `validation` block holds a `condition` that must evaluate to `true` and an `error_message` shown
when it does not.

```bash
terraform plan -var 'instance_type=m5.large'
```

**Expected output**

```text
Error: Invalid value for variable

  on variables.tf line 17:
  17: variable "instance_type" {
    ├────────────────
    │ var.instance_type is "m5.large"

instance_type must be a t3 size, for example t3.micro.

This was checked by the validation rule at variables.tf:23,3-13.
```

Note the heading: `Invalid value for variable`, not `for input variable`. A type mismatch and a
failed validation are different errors. Terraform echoes the offending value, prints your own
message, and cites the rule's position.

### Step 18 — Trip the validation rule on a collection

Validation is not limited to primitives. The rule on `disks` checks every element:

```bash
grep -A 3 'condition.*alltrue' variables.tf
```

**Expected output**

```text
    condition     = alltrue([for d in var.disks : d.size_gb >= 8])
    error_message = "Every disk needs size_gb of at least 8."
  }
}
```

```bash
terraform plan -var 'disks=[{device="/dev/sdb",size_gb=4}]'
```

**Expected output**

```text
Error: Invalid value for variable

  on variables.tf line 96:
  96: variable "disks" {
    ├────────────────
    │ var.disks is list of object with 1 element

Every disk needs size_gb of at least 8.

This was checked by the validation rule at variables.tf:107,3-13.
```

`alltrue()` over a `for` expression is the standard way to validate a collection: build a list of
booleans, one per element, and require them all. Because the value is a whole collection, Terraform
describes it by shape rather than quoting it.

### Step 19 — Read the locals block

```bash
sed -n '/^locals {/,/^}/p' main.tf
```

**Expected output**

```text
locals {
  common_tags = merge(var.tags, {
    Name = var.server_name
    Lab  = "lab06"
  })

  # coalesce() returns the first non-null, non-empty argument, so a null variable
  # falls through to the fallback.
  contact = coalesce(var.owner_email, "unset@example.invalid")

  # null and "" are different values, and only an equality test tells them apart.
  owner_email_state = (
    var.owner_email == null ? "null: no value was supplied" :
    var.owner_email == "" ? "empty string: a value was supplied and it is blank" :
    "set: ${var.owner_email}"
  )

  # Numbers support arithmetic; the same digits held as a string would not.
  total_disk_gb = var.root_volume_gb + sum([for d in var.disks : d.size_gb])

  # Same default value in both variables, different element count.
  list_vs_set = {
    list_length = length(var.role_list)
    set_length  = length(var.role_set)
    first_item  = var.role_list[0]
  }
}
```

You reference a variable as `var.NAME` and a local as `local.NAME`. The instance sets
`tags = local.common_tags`, so the tagging rule is written once no matter how many resources later
use it.

### Step 20 — Watch `merge()` build the tag map

```bash
echo 'var.tags' | terraform console
echo 'local.common_tags' | terraform console
```

**Expected output**

```text
tomap({
  "Environment" = "training"
  "Owner" = "platform-team"
})
{
  "Environment" = "training"
  "Lab" = "lab06"
  "Name" = "lab06-web"
  "Owner" = "platform-team"
}
```

Two tags went in and four came out. This works before anything exists in AWS, because locals and
variables are computed entirely inside Terraform. It is the cheapest way to check tagging logic.

### Step 21 — Read the network resources

Everything so far was a value inside Terraform. These are the three AWS resources the instance needs
before it can exist.

```bash
sed -n '/^# A VPC of its own/,/^}/p;/^resource "aws_subnet"/,/^}/p' main.tf
```

**Expected output**

```text
# A VPC of its own, so the lab never depends on the account having a default VPC.
resource "aws_vpc" "main" {
  cidr_block         = var.vpc_cidr
  enable_dns_support = true
  tags               = local.common_tags
}
resource "aws_subnet" "main" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.subnet_cidr
  availability_zone = var.subnet_az
  tags              = local.common_tags
}
```

An EC2 instance does not launch into a region or into a VPC — it launches into a **subnet**, which is
one address range inside one VPC in one availability zone. An `aws_instance` with no `subnet_id` is
not "subnet-free"; AWS quietly substitutes a subnet of the account's *default VPC*, and a fresh
training account often has no default VPC. `terraform plan` cannot see that, so the run fails only at
apply, with `VPCIdNotSpecified`. Declaring `subnet_id` removes the guesswork: this lab creates the
network it uses.

The third resource is the security group, which is a stateful firewall attached to the instance:

```bash
sed -n '/^resource "aws_security_group"/,/^}/p' main.tf
```

**Expected output**

```text
resource "aws_security_group" "instance" {
  name        = "${var.server_name}-sg"
  description = "Lab 06 instance security group"
  vpc_id      = aws_vpc.main.id
  tags        = local.common_tags

  ingress {
    description = "SSH from inside the VPC only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

Note what `cidr_blocks = [var.vpc_cidr]` means: port 22 is open to `10.0.0.0/16` and nothing else, so
only something already inside this VPC can connect. **You will not be able to SSH to this instance
from your laptop, and that is intentional.** There is no internet gateway, no route table entry to
one, and no public IP, so the instance has no path to or from the internet in either direction. Lab
21 builds the public version — internet gateway, route table, public IP — as the track's capstone.

Each of the three carries `tags = local.common_tags`, so the tag lesson from Step 19 applies to the
whole configuration and not just the instance.

### Step 22 — Validate

```bash
terraform validate
```

**Expected output**

```text
Success! The configuration is valid.
```

This checks types and references without contacting AWS, so a misspelled `var.` name is caught here
rather than halfway through an apply. It does **not** check variable *values* — every error you
triggered above needed a `plan`.

### Step 23 — Plan with the defaults

```bash
terraform plan
```

**Expected output**

```text
Plan: 4 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + api_token          = (sensitive value)
  + applied_tags       = {
      + Environment = "training"
      + Lab         = "lab06"
      + Name        = "lab06-web"
      + Owner       = "platform-team"
    }
  + contact            = "unset@example.invalid"
  + instance_arn       = (known after apply)
  + instance_id        = (known after apply)
  + list_vs_set        = {
      + first_item  = "web"
      + list_length = 3
      + set_length  = 2
    }
  + owner_email_state  = "null: no value was supplied"
  + prod_instance_type = "t3.small"
  + profile_department = "unassigned"
  + public_ip          = (known after apply)
  + release_build      = 3
  + security_group_id  = (known after apply)
  + subnet_id          = (known after apply)
  + total_disk_gb      = 38
  + vpc_id             = (known after apply)
```

Every variable has a default, so the plan works with no input from you. Eighteen variables and four
resources — the VPC, subnet, security group, and instance — because the type lessons themselves cost
nothing. `total_disk_gb = 38` is `8 + 10 + 20`, which only works because those are `number` values.

### Step 24 — Override one value on the command line

```bash
terraform plan -var 'server_name=lab06-cli-web'
```

**Expected output**

```text
  + applied_tags       = {
      + Environment = "training"
      + Lab         = "lab06"
      + Name        = "lab06-cli-web"
      + Owner       = "platform-team"
    }
```

`merge()` replaced one key and left the rest, and `-var` beat the default. Lab 07 covers the other
ways to supply values and the order Terraform applies them in.

### Step 25 — Apply

```bash
terraform apply
```

Type `yes` at the prompt.

**Expected output**

```text
aws_vpc.main: Creating...
aws_vpc.main: Creation complete after 4s [id=vpc-0db5e7a147fcfb091]
aws_subnet.main: Creating...
aws_security_group.instance: Creating...
aws_subnet.main: Creation complete after 2s [id=subnet-0717ff18470786f8a]
aws_security_group.instance: Creation complete after 5s [id=sg-0cd5e816e5ecd7a9c]
aws_instance.web: Creating...
aws_instance.web: Still creating... [00m10s elapsed]
aws_instance.web: Creation complete after 17s [id=i-051e98415c2e23c5f]

Apply complete! Resources: 4 added, 0 changed, 0 destroyed.

Outputs:

api_token = <sensitive>
applied_tags = {
  "Environment" = "training"
  "Lab" = "lab06"
  "Name" = "lab06-web"
  "Owner" = "platform-team"
}
contact = "unset@example.invalid"
instance_arn = "arn:aws:ec2:us-east-2:908936660945:instance/i-051e98415c2e23c5f"
instance_id = "i-051e98415c2e23c5f"
list_vs_set = {
  "first_item" = "web"
  "list_length" = 3
  "set_length" = 2
}
owner_email_state = "null: no value was supplied"
prod_instance_type = "t3.small"
profile_department = "unassigned"
public_ip = ""
release_build = 3
security_group_id = "sg-0cd5e816e5ecd7a9c"
subnet_id = "subnet-0717ff18470786f8a"
total_disk_gb = 38
vpc_id = "vpc-0db5e7a147fcfb091"
```

Your account number and every ID will differ. `api_token` printed as `<sensitive>`. Terraform created
the VPC first, then the subnet and security group in parallel, then the instance — it derived that
order from the `aws_vpc.main.id` and `aws_subnet.main.id` references, not from the order the blocks
appear in the file.

`public_ip` is the empty string, not an address. The instance has no public IP, so there is nothing to
connect to from outside; the private address is reachable only from inside `10.0.0.0/16`.

### Step 26 — Read outputs back without applying

```bash
terraform output
terraform output list_vs_set
```

Outputs are stored in state, so you can re-read them at any time. Naming one output prints only that
one, keeping its type formatting.

### Step 27 — Read a single output for scripting

```bash
terraform output -raw instance_id
```

**Expected output**

```text
i-051e98415c2e23c5f
```

`-raw` prints the bare value with no quotes, which is what you want when feeding it into another
command. It also works on a sensitive output — asking by name is always allowed:

```bash
terraform output -raw api_token
```

**Expected output**

```text
lab06-placeholder-not-a-real-token
```

### Step 28 — Confirm the tags reached AWS

```bash
aws ec2 describe-tags \
  --filters "Name=resource-id,Values=$(terraform output -raw instance_id)" \
  --query 'Tags[].[Key,Value]' --output text
```

**Expected output**

```text
Environment	training
Lab	lab06
Name	lab06-web
Owner	platform-team
```

The command substitution is why Step 27 mattered. All four tags from `local.common_tags` are on the
real instance, which closes the loop from variable to local to resource to AWS.

### Step 29 — Confirm the instance is where you put it and is not exposed

```bash
aws ec2 describe-security-groups \
  --group-ids "$(terraform output -raw security_group_id)" \
  --query 'SecurityGroups[].IpPermissions[].[IpProtocol,FromPort,ToPort,IpRanges[].CidrIp|[0]]' \
  --output text
```

**Expected output**

```text
tcp	22	22	10.0.0.0/16
```

One ingress rule, and its source is the VPC's own range. If that last column ever reads `0.0.0.0/0`,
port 22 is open to the entire internet — check it on every security group you write.

```bash
aws ec2 describe-instances \
  --instance-ids "$(terraform output -raw instance_id)" \
  --query 'Reservations[].Instances[].[SubnetId,PrivateIpAddress,PublicIpAddress]' \
  --output text
```

**Expected output**

```text
subnet-0717ff18470786f8a	10.0.1.205	None
```

The instance is in the subnet Terraform created, holds a private `10.0.1.x` address, and has no public
address at all — `None` is AWS reporting the field absent. Do not try to SSH to it; nothing about this
configuration makes that possible.

### Step 30 — Destroy

```bash
terraform destroy
```

Type `yes` at the prompt.

**Expected output**

```text
Destroy complete! Resources: 4 destroyed.
```

Terraform tears down in reverse dependency order: instance, then security group and subnet, then the
VPC.

## Done when

- [ ] You can name the three primitive, three collection, and two structural types
- [ ] `tonumber("abc")` failed while `"8" + 1` returned `9`
- [ ] `-var 'root_volume_gb=large'` produced `Invalid value for input variable ... a number is required`
- [ ] `var.role_list` printed three entries and `var.role_set` printed two, from the same default
- [ ] `var.server_profile` printed five attributes although the default set three
- [ ] An object missing a required attribute and a tuple of the wrong length both failed
- [ ] `var.environments["prod"].instance_type` returned `"t3.small"`
- [ ] `type(var.freeform)` printed an inferred type you never declared
- [ ] `owner_email_state` distinguished `null` from `""`
- [ ] `var.api_token` printed `(sensitive value)` in the console and `<sensitive>` after apply
- [ ] Both validation rules rejected bad input with your own error messages
- [ ] `terraform plan` succeeds using defaults alone and reports `4 to add`
- [ ] `describe-tags` returns four tags, including `Lab = lab06`
- [ ] `describe-security-groups` shows one ingress rule, `tcp 22` from the VPC CIDR and not `0.0.0.0/0`
- [ ] `describe-instances` shows the instance in your own subnet with no public IP
- [ ] You can explain why the instance needs a `subnet_id` and why you cannot SSH to it
- [ ] `terraform destroy` reports `4 destroyed`

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `No value for required variable` | Variable has no `default` and none was supplied | Add `default`, or pass `-var 'name=value'` |
| `Unsuitable value for var.X ... a number is required` | Wrong type passed for a primitive | Match the `type` in `variables.tf` |
| `Unsuitable value for var.X ... attribute "y" is required` | Object value missing a non-`optional()` attribute | Supply every required attribute |
| `Unsuitable value for var.X ... tuple required` | Tuple has the wrong length or wrong types per position | Match the declared positions exactly |
| `Invalid value for variable` plus your own message | A `validation` `condition` returned false | Read the quoted value and the rule it cites |
| `cannot convert "abc" to number` | Conversion has no unambiguous interpretation | Pass a numeric literal |
| Duplicates unexpectedly gone | Variable declared `set(string)` rather than `list(string)` | Change the `type`, or accept deduplication |
| `Invalid index` on a set | Sets have no positions | `tolist(var.role_set)[0]`, or use a list |
| `Output refers to sensitive values` | An output derives from a sensitive variable | Add `sensitive = true` to the output |
| `Reference to undeclared local value` | Used `local.x` before adding it to the `locals` block | Declare it in `locals` |
| `No valid credential sources found` | Credentials not exported in this shell | Re-export the keys from Lab 00 |
| `Output "instance_id" not found` | `apply` has not run, or you are in another directory | `pwd`, then `terraform apply` |
| `InvalidAMIID.NotFound` | AMI lookup returned nothing in this region | Confirm `aws_region` is `us-east-2` |
| `InvalidSubnet.Range: The CIDR '...' is invalid` on `aws_subnet.main` | `subnet_cidr` is not inside `vpc_cidr` | Pick a range within `vpc_cidr`, e.g. `10.0.1.0/24` inside `10.0.0.0/16` |
| `InvalidParameterValue: Value (...) for parameter availabilityZone is invalid` | `subnet_az` is not a zone of `aws_region` | Use a zone the error lists — `us-east-2a`, `us-east-2b`, or `us-east-2c` |
| `destroy` sits on `aws_subnet.main: Still destroying...` for many minutes, then `Request cancelled` | Something Terraform does not manage still lives in the subnet, so AWS refuses the delete and the provider retries until it times out | Find it with `aws ec2 delete-subnet --subnet-id <id>`, which fails immediately and names the cause: `DependencyViolation: The subnet '<id>' has dependencies and cannot be deleted`. Delete the leftover — usually a network interface, from `aws ec2 describe-network-interfaces --filters Name=subnet-id,Values=<id>` — then re-run `terraform destroy` |
| `DependencyViolation: The vpc '<id>' has dependencies and cannot be deleted` | Same cause one level up: a subnet, security group, or interface inside the VPC survived | Clear the contents first; a `terraform destroy` that completes does this in the right order by itself |

## Cleanup

```bash
terraform destroy
rm -f /tmp/null-test.tfvars
```

## Next steps

- Deep dive: [docs/05-variables.md](../docs/05-variables.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab06-variables-outputs)
- Continue to [Lab 07 — tfvars and Secrets](lab07-tfvars-secrets.md)
