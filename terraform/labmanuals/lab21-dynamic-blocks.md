# Lab 21 — Dynamic Blocks

| | |
|---|---|
| **Goal** | Generate a security group's ingress rules from a map with a `dynamic` block, instead of writing one `ingress` block per port by hand. |
| **Time** | 40–50 minutes |
| **Tier** | Advanced |
| **Files** | `terraform/labs/lab21-dynamic-blocks/` |

## Overview

> **This lab requires a default VPC.** It is one of only two in the track that does — Lab 15 is
> the other. The security group here declares no `vpc_id`, because the lesson is the `dynamic`
> block and not the network, so AWS places the group in the region's *default* VPC. Many AWS
> accounts, including freshly issued lab and sandbox accounts, ship without one. `terraform plan`
> cannot detect this and passes cleanly; only the apply fails, with
> `VPCIdNotSpecified: No default VPC for this user`. Check before you begin:
>
> ```bash
> aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[].VpcId' --output text
> ```
>
> If that prints nothing, the account has none. Create one once, and it is reused by every later
> run:
>
> ```bash
> aws ec2 create-default-vpc
> ```


Sometimes a resource needs many copies of a *block inside it*. A **security group** is the clearest
example: it is an AWS firewall, and each rule you want is a separate `ingress` block nested in the
same `aws_security_group` resource. Two ports means two near-identical blocks, and adding a third
means editing HCL. [Lab 10's](lab10-capstone-vpc-ec2.md) capstone security group needed exactly one
rule, so it was written out literally; this lab is what you reach for when there are several.

A **dynamic block** solves that. `dynamic "ingress"` takes a collection in `for_each` and generates
one real `ingress` block per element, using the `content` block as the template. Adding a port
becomes a data change, not a code change. **Ingress** means inbound traffic; **egress** means
outbound.

Note that `for_each` appears here as an argument *inside* a `dynamic` block, generating nested
blocks within one resource. The `for_each` **meta-argument**, which makes many copies of a whole
resource, is a different thing and comes later in
[Lab 24](lab24-count-foreach-buckets.md). The map-and-object handling from
[Lab 11](lab11-collections.md) is all you need here.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `var.ingress_rules` | A map of two rules: HTTP 80, HTTPS 443 | Free |
| `aws_security_group.service` | One security group with two generated ingress blocks | Free |
| Static `egress` block | Written the ordinary way, for comparison | Free |
| 2 outputs | `security_group_id`, `ingress_ports` | — |

## Before you start

- [ ] Lab 20 completed ([lab20-remote-state-consumer.md](lab20-remote-state-consumer.md))
- [ ] You can read a `map(object(...))` and reach one attribute of one entry (Lab 11)
- [ ] AWS credentials exported and `aws sts get-caller-identity` succeeds
- [ ] Working directory: `../labs/lab21-dynamic-blocks/`
- [ ] A default VPC exists in `us-east-2` — this security group has no `vpc_id`, so it needs one, for the reason given in [Lab 03](lab03-first-ec2.md):

```bash
aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[].VpcId' --output text
```

If that prints nothing, run `aws ec2 create-default-vpc` once. The plan in Step 8 passes either
way; only the apply fails.

## Steps

### Step 1 — Read the rule data

```bash
cd terraform/labs/lab21-dynamic-blocks
sed -n '/variable "ingress_rules"/,$p' variables.tf
```

`variables.tf` also declares `aws_region`, defaulting to `us-east-2`; the command above skips it to
keep the rule data in view.

**Expected output** *(trimmed — the `https` entry follows the same shape)*

```text
variable "ingress_rules" {
  type = map(object({
    port        = number
    cidr_blocks = list(string)
    description = string
  }))
  description = "One entry per inbound rule. dynamic turns each entry into an ingress block. No SSH rule: nothing in this lab connects to a host."
  default = {
    http = {
      port        = 80
      cidr_blocks = ["10.0.0.0/8"]
      description = "internal HTTP"
    }
...
  }
}
```

A map with two keys, each value an object with `port`, `cidr_blocks`, and `description`. All the
information that varies between rules lives here in data, which is the whole idea.

There is no port 22 entry. No step in this lab logs into anything, so an SSH rule would be an
opening nothing uses — and the rules are scoped to `10.0.0.0/8` rather than `0.0.0.0/0` for the
same reason. Add a rule when something needs it.

### Step 2 — Inspect one rule in the console

```bash
echo 'var.ingress_rules["https"]' | terraform console
```

**Expected output**

```text
{
  "cidr_blocks" = tolist([
    "10.0.0.0/8",
  ])
  "description" = "internal HTTPS"
  "port" = 443
}
```

One map entry is one object with three attributes. Inside the `dynamic` block you will reach these as
`ingress.value.port`, `ingress.value.cidr_blocks`, and `ingress.value.description`.

### Step 3 — Read the dynamic block

```bash
grep -A 12 'dynamic "ingress"' main.tf
```

**Expected output**

```text
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
```

Three things to notice. The label after `dynamic` is the name of the block being generated, so
`dynamic "ingress"` produces `ingress` blocks. Inside `content`, the iterator is named after that
label — you write `ingress.value`, not `each.value`, which is the single most common mistake here.
And `content` is the template: written once, stamped out per element.

### Step 4 — Read the static block for contrast

```bash
grep -A 7 'egress {' main.tf
```

**Expected output**

```text
  egress {
    description = "all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
```

A plain nested block with fixed values. There is exactly one outbound rule and it never varies, so a
dynamic block would only add noise. Use `dynamic` when the number of blocks depends on data; write
the block out when it does not.

### Step 5 — Initialize

```bash
terraform init
```

**Expected output**

```text
Terraform has been successfully initialized!
```

### Step 6 — Validate

```bash
terraform validate
```

**Expected output**

```text
Success! The configuration is valid.
```

`validate` confirms the `dynamic` block and its `content` are well formed. It cannot tell you the
generated rules are the ones you wanted — that is what the plan in Step 8 is for.

### Step 7 — Preview the port list the output will produce

```bash
echo 'sort([for rule in values(var.ingress_rules) : tostring(rule.port)])' | terraform console
```

**Expected output**

```text
tolist([
  "443",
  "80",
])
```

This is the expression behind the `ingress_ports` output. `443` comes before `80` because `sort()`
compares strings, not numbers, and `"4"` sorts before `"8"`. Worth knowing before you see it in the
apply output and assume something is broken.

### Step 8 — Plan and count the generated blocks

```bash
terraform plan
```

**Expected output**

```text
      + ingress                = [
          + {
              + cidr_blocks      = [
                  + "10.0.0.0/8",
                ]
              + description      = "internal HTTP"
              + from_port        = 80
              + protocol         = "tcp"
              + to_port          = 80
            },
          + {
              + cidr_blocks      = [
                  + "10.0.0.0/8",
                ]
              + description      = "internal HTTPS"
              + from_port        = 443
              + protocol         = "tcp"
              + to_port          = 443
            },
        ]

Plan: 1 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + ingress_ports     = [
      + "443",
      + "80",
    ]
  + security_group_id = (known after apply)
```

One resource, but the `ingress` section of the plan lists two separate entries — ports 80 and 443
— each carrying its own description. The plan is where you confirm the generation did what you
meant, because the `.tf` file no longer shows the rules literally.

### Step 9 — Apply

```bash
terraform apply
```

Type `yes` at the prompt.

**Expected output**

```text
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

ingress_ports = [
  "443",
  "80",
]
security_group_id = "sg-0abc123def4567890"
```

Your security group ID will differ. The port order is the string sort from Step 7.

### Step 10 — Confirm the ports in AWS

```bash
aws ec2 describe-security-groups \
  --group-ids "$(terraform output -raw security_group_id)" \
  --query 'SecurityGroups[0].IpPermissions[].FromPort' --output text
```

**Expected output**

```text
80	443
```

Two separate real rules exist in AWS, generated from two map entries. The order AWS returns them
in is not guaranteed and may differ from this.

### Step 11 — Confirm the descriptions came through

```bash
aws ec2 describe-security-groups \
  --group-ids "$(terraform output -raw security_group_id)" \
  --query 'SecurityGroups[0].IpPermissions[]' --output json
```

Read the JSON that comes back: each permission object holds a `FromPort` and an `IpRanges` list, and
each range carries the `Description` your map supplied — `internal HTTP` and `internal HTTPS`.
Descriptions are the strongest evidence the generation is per element rather than
one merged rule, because each one differs.

### Step 12 — Add a rule by changing data only

```bash
terraform plan -var 'ingress_rules={
  http  = { port = 80,   cidr_blocks = ["10.0.0.0/8"], description = "internal HTTP" }
  https = { port = 443,  cidr_blocks = ["10.0.0.0/8"], description = "internal HTTPS" }
  pg    = { port = 5432, cidr_blocks = ["10.0.0.0/8"], description = "internal Postgres" }
}'
```

**Expected output**

```text
Plan: 0 to add, 1 to change, 0 to destroy.
```

The plan now shows a third ingress rule on port 5432, and no `.tf` file was edited. In a real
project that map would live in `terraform.tfvars`, so opening a port becomes a reviewable one-line
data change rather than a code change.

### Step 13 — Know when not to use a dynamic block

Dynamic blocks are harder to read than plain blocks, and error messages point at the generated block
rather than at your `content` template, which makes debugging indirect. HashiCorp's own advice is to
use them sparingly: reach for `dynamic` when a block count genuinely comes from data, as it does
here, and write blocks out literally when it does not — as the `egress` block in Step 4 does.

### Step 14 — Destroy

```bash
terraform destroy
```

Type `yes` at the prompt.

**Expected output**

```text
Destroy complete! Resources: 1 destroyed.
```

## Done when

- [ ] `terraform validate` succeeds
- [ ] The console shows one map entry as an object with three attributes
- [ ] You can explain why `443` sorts before `80`
- [ ] The plan shows two ingress entries generated from one `dynamic` block
- [ ] `apply` outputs a `sg-` ID and the two ports
- [ ] `describe-security-groups` returns ports 80 and 443 with distinct descriptions
- [ ] Passing a three-entry map produces a third rule with no file edits
- [ ] `terraform destroy` reports `1 destroyed`

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `Blocks of type "content" are not expected here` | `content` used outside a `dynamic` block | Only `dynamic` blocks take `content` |
| `Reference to undeclared resource: each` | Used `each.value` inside `dynamic "ingress"` | The iterator is the label: `ingress.value` |
| `Unsupported argument` inside `content` | Argument is not valid for a real `ingress` block | `content` accepts only the block's own arguments |
| `Invalid value for input variable` | A map entry is missing `port`, `cidr_blocks`, or `description` | Every entry needs all three |
| `Invalid dynamic for_each` | Passed a list of objects | Convert to a map, or wrap with `toset()` |
| `InvalidGroup.Duplicate` | A group with this name already exists | `name_prefix` avoids this; destroy the old group |
| `VPCIdNotSpecified: No default VPC for this user` on `CreateSecurityGroup`, after a clean plan | The group declares no `vpc_id`, so AWS puts it in the default VPC — and this account has none ([Lab 03](lab03-first-ec2.md)) | `aws ec2 create-default-vpc`, then `terraform apply` again |

## Cleanup

```bash
terraform destroy
```

## Next steps

- Deep dive: [docs/14-dynamic-blocks.md](../docs/14-dynamic-blocks.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab21-dynamic-blocks)
- Continue to [Lab 22 — EC2 with remote state in S3](lab22-ec2-s3-backend.md)
