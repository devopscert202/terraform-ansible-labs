# Lab 07 — tfvars and Secrets

| | |
|---|---|
| **Goal** | Supply variable values from a `terraform.tfvars` file, pass a secret through a `TF_VAR_` environment variable, see `sensitive = true` redact it, and work out which source wins when two disagree. |
| **Time** | 40–50 minutes |
| **Tier** | Intermediate |
| **Files** | `terraform/labs/lab07-tfvars-secrets/` |

## Overview

Lab 06 passed values with `-var` on the command line, which is fine for one value and painful for
ten. A **tfvars file** is a plain file of `name = value` lines that Terraform reads automatically
when it is called `terraform.tfvars`. That solves the typing problem but creates a new one: a file
of settings is exactly where people accidentally commit passwords.

This lab separates the two kinds of input. Ordinary settings go in `terraform.tfvars`. The secret
never touches a file — it arrives through the `TF_VAR_db_password` environment variable, and its
variable is marked `sensitive = true` so Terraform refuses to print it. You will then set the same
variable from two places at once to see the precedence order for yourself.

The three ordinary settings are not merely printed. They become tags on a real VPC and a real
subnet, so after `apply` you can read `Project`, `Environment` and `CostCode` back off AWS and see
that the file on your laptop reached the cloud. `db_password` is deliberately kept out of every tag,
for a reason Step 9 makes explicit.

A VPC and a subnet cost nothing, but they are real, so this lab needs AWS credentials.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| 3 plain variables | `project`, `environment`, `cost_code` — set from `terraform.tfvars` | Free |
| 1 sensitive variable | `db_password` — set from the environment | Free |
| 4 network variables | `aws_region`, `vpc_cidr`, `subnet_cidr`, `subnet_az` — all defaulted | Free |
| 2 validation rules | Reject a bad `environment` or a bad `cost_code` | Free |
| `aws_vpc.main` | A real VPC tagged from the tfvars values | Free |
| `aws_subnet.main` | A real subnet tagged from the same values | Free |
| 6 outputs | `settings`, `db_password` (redacted), `db_password_length`, `vpc_id`, `vpc_tags`, `subnet_id` | Free |

Two managed resources, no data sources.

## Before you start

- [ ] Lab 06 completed ([lab06-variables-outputs.md](lab06-variables-outputs.md))
- [ ] AWS credentials configured for `us-east-2` (`aws sts get-caller-identity` succeeds)
- [ ] Working directory: `../labs/lab07-tfvars-secrets/`

## Steps

### Step 1 — See what is and is not committed

```bash
cd terraform/labs/lab07-tfvars-secrets
ls
grep tfvars ../../../.gitignore
```

**Expected output**

```text
main.tf
outputs.tf
terraform.tfvars.example
variables.tf
```

```text
**/*.tfvars
!**/*.tfvars.example
```

There is no `terraform.tfvars` yet, only a `.example`. The repository ignores every `*.tfvars` file
and makes one exception for `*.tfvars.example`. So the real file with real values is never committed,
while a committed template shows the next person which variables exist. Every lab in this track that
takes variables ships a `terraform.tfvars.example` for that reason.

### Step 2 — Read the variable declarations

```bash
cat variables.tf
```

**Expected output**

```text
variable "project" {
  type        = string
  description = "Project name. Set in terraform.tfvars."
}
...
variable "db_password" {
  type        = string
  description = "Database password. Never put this in a committed file; export TF_VAR_db_password instead."
  sensitive   = true
}
```

Those four are declared first and none has a `default`, so all four are mandatory — this is the only
lab besides Lab 15 that requires you to create a tfvars file. Only `db_password` carries
`sensitive = true`. Two of the others carry a `validation` block, which you will trip in Steps 14
and 15.

Four further variables follow them in the file — `aws_region`, `vpc_cidr`, `subnet_cidr` and
`subnet_az` — describing the network. Every one carries a default, so they need no tfvars entry.

### Step 3 — Read the committed template

```bash
cat terraform.tfvars.example
```

**Expected output**

```text
# Copy to terraform.tfvars, then edit. terraform.tfvars is gitignored.
# This .example file is committed, so it must never contain a real secret.

project     = "platform"
environment = "dev"
cost_code   = "123"

# db_password is deliberately absent. Supply it at runtime:
#   export TF_VAR_db_password='not-a-real-password'
```

The template sets three variables and deliberately omits the fourth. A committed template that
listed `db_password = "..."` would defeat the whole point, so it documents the runtime method
instead.

### Step 4 — Create your real tfvars file

```bash
cp terraform.tfvars.example terraform.tfvars
```

Terraform loads a file named exactly `terraform.tfvars` on its own — you do not pass a flag for it.
Any other name needs `-var-file`.

### Step 5 — Initialize

```bash
terraform init
```

**Expected output** *(trimmed)*

```text
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.100.0...
- Installed hashicorp/aws v5.100.0 (signed by HashiCorp)

Terraform has been successfully initialized!
```

### Step 6 — Plan without the secret, and watch Terraform ask for it

```bash
terraform plan
```

**Expected output**

```text
var.db_password
  Database password. Never put this in a committed file; export TF_VAR_db_password instead.

  Enter a value:
```

Three variables came from `terraform.tfvars`, so Terraform does not ask about them. The fourth is
mandatory and unset, so Terraform prompts interactively and shows the variable's `description` — one
concrete reason every variable should have one. Press `Ctrl-C` to cancel rather than typing a value.

In a non-interactive context such as CI there is no prompt, and you get this instead:

```text
Error: No value for required variable

  on variables.tf line 26:
  26: variable "db_password" {

The root module input variable "db_password" is not set, and has no default
value.
```

### Step 7 — Supply the secret through the environment

```bash
export TF_VAR_db_password='not-a-real-password'
terraform plan
```

**Expected output**

```text

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # aws_subnet.main will be created
  + resource "aws_subnet" "main" {
      + arn                                            = (known after apply)
      + assign_ipv6_address_on_creation                = false
      + availability_zone                              = "us-east-2a"
      + availability_zone_id                           = (known after apply)
      + cidr_block                                     = "10.7.1.0/24"
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
          + "CostCode"    = "123"
          + "Environment" = "dev"
          + "Lab"         = "lab07"
          + "Name"        = "platform-dev-subnet"
          + "Project"     = "platform"
        }
      + tags_all                                       = {
          + "CostCode"    = "123"
          + "Environment" = "dev"
          + "Lab"         = "lab07"
          + "Name"        = "platform-dev-subnet"
          + "Project"     = "platform"
        }
      + vpc_id                                         = (known after apply)
    }

  # aws_vpc.main will be created
  + resource "aws_vpc" "main" {
      + arn                                  = (known after apply)
      + cidr_block                           = "10.7.0.0/16"
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
          + "CostCode"    = "123"
          + "Environment" = "dev"
          + "Lab"         = "lab07"
          + "Name"        = "platform-dev"
          + "Project"     = "platform"
        }
      + tags_all                             = {
          + "CostCode"    = "123"
          + "Environment" = "dev"
          + "Lab"         = "lab07"
          + "Name"        = "platform-dev"
          + "Project"     = "platform"
        }
    }

Plan: 2 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + db_password        = (sensitive value)
  + db_password_length = 19
  + settings           = {
      + cost_code   = "123"
      + environment = "dev"
      + project     = "platform"
    }
  + subnet_id          = (known after apply)
  + vpc_id             = (known after apply)
  + vpc_tags           = {
      + CostCode    = "123"
      + Environment = "dev"
      + Lab         = "lab07"
      + Name        = "platform-dev"
      + Project     = "platform"
    }

─────────────────────────────────────────────────────────────────────────────

Note: You didn't use the -out option to save this plan, so Terraform can't
guarantee to take exactly these actions if you run "terraform apply" now.
```

`Plan: 2 to add, 0 to change, 0 to destroy.` The VPC and subnet appear with their tags already
resolved — `Project = "platform"`, `Environment = "dev"`, `CostCode = "123"` — so you can see the
tfvars values in the plan before anything is created. `db_password` shows as `(sensitive value)`.

Terraform reads any environment variable named `TF_VAR_` plus the variable name. The value lives
only in your shell session, so there is no file to leak and nothing to commit. No prompt this time.

### Step 8 — Apply and watch the redaction

```bash
terraform apply -auto-approve
```

**Expected output**

```text

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # aws_subnet.main will be created
  + resource "aws_subnet" "main" {
      + arn                                            = (known after apply)
      + assign_ipv6_address_on_creation                = false
      + availability_zone                              = "us-east-2a"
      + cidr_block                                     = "10.7.1.0/24"

[... the two resource bodies are identical to the plan in Step 7 and are elided here ...]

Plan: 2 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + db_password        = (sensitive value)
  + db_password_length = 19
  + settings           = {
      + cost_code   = "123"
      + environment = "dev"
      + project     = "platform"
    }
  + subnet_id          = (known after apply)
  + vpc_id             = (known after apply)
  + vpc_tags           = {
      + CostCode    = "123"
      + Environment = "dev"
      + Lab         = "lab07"
      + Name        = "platform-dev"
      + Project     = "platform"
    }
aws_vpc.main: Creating...
aws_vpc.main: Creation complete after 4s [id=vpc-0566fd74a48916695]
aws_subnet.main: Creating...
aws_subnet.main: Creation complete after 1s [id=subnet-0ce6dc1045605b580]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

db_password = <sensitive>
db_password_length = 19
settings = {
  "cost_code" = "123"
  "environment" = "dev"
  "project" = "platform"
}
subnet_id = "subnet-0ce6dc1045605b580"
vpc_id = "vpc-0566fd74a48916695"
vpc_tags = tomap({
  "CostCode" = "123"
  "Environment" = "dev"
  "Lab" = "lab07"
  "Name" = "platform-dev"
  "Project" = "platform"
})
```

`Apply complete! Resources: 2 added, 0 changed, 0 destroyed.`

`db_password` prints as `<sensitive>` because both the variable and the output are marked
`sensitive = true`. `db_password_length` is `19` — proof the value arrived, without showing it. That
output had to be wrapped in `nonsensitive()`, because anything derived from a sensitive value is
treated as sensitive too, and `terraform validate` refuses to expose it otherwise.

`settings` prints the three ordinary values, and `vpc_tags` prints the same three as AWS recorded
them. Those are two different things: the first is what you supplied, the second is what the cloud
now holds.

### Step 9 — Confirm the tfvars values reached AWS

Do not take Terraform's word for it. Ask AWS directly.

```bash
aws ec2 describe-vpcs \
  --region us-east-2 \
  --filters 'Name=tag:Lab,Values=lab07' \
  --query 'Vpcs[].Tags' --output table
```

**Expected output**

```text
---------------------------------
|         DescribeVpcs          |
+--------------+----------------+
|      Key     |     Value      |
+--------------+----------------+
|  CostCode    |  123           |
|  Name        |  platform-dev  |
|  Lab         |  lab07         |
|  Environment |  dev           |
|  Project     |  platform      |
+--------------+----------------+
```

`Project`, `Environment` and `CostCode` are there, with the values from your `terraform.tfvars`. A
line you typed in a local file is now metadata on a real network in a real account. That is what a
variable is *for*; printing it back was never the goal.

Note what is **not** there: `db_password`. Tags are readable by anyone with describe permission on
the account, so a secret in a tag is a published secret. That is why `common_tags` in `main.tf`
omits it.

### Step 10 — Read the secret back out

```bash
terraform output -raw db_password
```

**Expected output**

```text
not-a-real-password
```

Asking for the value by name gives it to you. `sensitive = true` prevents accidental display in
plans, applies, and logs. It is not encryption and it is not access control.

### Step 11 — Find the secret in the state file

```bash
grep -o 'not-a-real-password' terraform.tfstate
```

**Expected output**

```text
not-a-real-password
```

You kept the secret out of git, and it landed in `terraform.tfstate` in clear text anyway. This is
why that file is gitignored too, and it is the problem Lab 08 examines in detail.

### Step 12 — Precedence: `-var` beats `terraform.tfvars`

```bash
terraform plan -var 'environment=prod'
```

**Expected output**

```text
aws_vpc.main: Refreshing state... [id=vpc-0566fd74a48916695]
aws_subnet.main: Refreshing state... [id=subnet-0ce6dc1045605b580]

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  ~ update in-place

Terraform will perform the following actions:

  # aws_subnet.main will be updated in-place
  ~ resource "aws_subnet" "main" {
        id                                             = "subnet-0ce6dc1045605b580"
      ~ tags                                           = {
            "CostCode"    = "123"
          ~ "Environment" = "dev" -> "prod"
            "Lab"         = "lab07"
          ~ "Name"        = "platform-dev-subnet" -> "platform-prod-subnet"
            "Project"     = "platform"
        }
      ~ tags_all                                       = {
          ~ "Environment" = "dev" -> "prod"
          ~ "Name"        = "platform-dev-subnet" -> "platform-prod-subnet"
            # (3 unchanged elements hidden)
        }
        # (19 unchanged attributes hidden)
    }

  # aws_vpc.main will be updated in-place
  ~ resource "aws_vpc" "main" {
        id                                   = "vpc-0566fd74a48916695"
      ~ tags                                 = {
            "CostCode"    = "123"
          ~ "Environment" = "dev" -> "prod"
            "Lab"         = "lab07"
          ~ "Name"        = "platform-dev" -> "platform-prod"
            "Project"     = "platform"
        }
      ~ tags_all                             = {
          ~ "Environment" = "dev" -> "prod"
          ~ "Name"        = "platform-dev" -> "platform-prod"
            # (3 unchanged elements hidden)
        }
        # (18 unchanged attributes hidden)
    }

Plan: 0 to add, 2 to change, 0 to destroy.

Changes to Outputs:
  ~ settings           = {
      ~ environment = "dev" -> "prod"
        # (2 unchanged attributes hidden)
    }
  ~ vpc_tags           = {
      ~ Environment = "dev" -> "prod"
      ~ Name        = "platform-dev" -> "platform-prod"
        # (3 unchanged attributes hidden)
    }

─────────────────────────────────────────────────────────────────────────────

Note: You didn't use the -out option to save this plan, so Terraform can't
guarantee to take exactly these actions if you run "terraform apply" now.
```

`terraform.tfvars` says `dev`. The command line says `prod`. The command line wins.

This plan is more interesting than a changed output. `Plan: 0 to add, 2 to change, 0 to destroy.`
Terraform proposes updating the `Environment` and `Name` tags on both the VPC and the subnet in
place, because a tag can be changed without replacing the resource. One overridden variable, two
real resources amended.

### Step 13 — Precedence: `terraform.tfvars` beats `TF_VAR_`

```bash
TF_VAR_environment=prod terraform plan
```

**Expected output**

```text
No changes. Your infrastructure matches the configuration.
```

The environment variable said `prod`, and nothing changed — `terraform.tfvars` still won with `dev`.
This one surprises people, so learn the full order now, highest priority first:

1. `-var` on the command line
2. `-var-file` on the command line
3. `terraform.tfvars`
4. `TF_VAR_` environment variable
5. The variable's `default`

Note the consequence for secrets: because `TF_VAR_` sits *below* tfvars, a stale variable exported in
your shell will be silently ignored if someone adds the same name to `terraform.tfvars`.

### Step 14 — Trip the `environment` validation rule

```bash
terraform plan -var 'environment=Production'
```

**Expected output**

```text
Error: Invalid value for variable

  on variables.tf line 6:
   6: variable "environment" {
    ├────────────────
    │ var.environment is "Production"

environment must be dev, test, or prod.

This was checked by the validation rule at variables.tf:10,3-13.
```

A `validation` block inside a `variable` rejects bad input before Terraform contacts any provider.
The error quotes the offending value, prints your own `error_message`, and points at the rule.

### Step 15 — Trip the `cost_code` validation rule

```bash
terraform plan -var 'cost_code=12345'
```

**Expected output**

```text
Error: Invalid value for variable

  on variables.tf line 16:
  16: variable "cost_code" {
    ├────────────────
    │ var.cost_code is "12345"

cost_code must contain exactly three characters.

This was checked by the validation rule at variables.tf:20,3-13.
```

Validation is not limited to a fixed list of allowed values. This rule uses `length()`, and any
expression returning `true` or `false` will work.

### Step 16 — Destroy, then clean up the secret and the tfvars file

```bash
terraform destroy -auto-approve
```

**Expected output**

```text
aws_vpc.main: Refreshing state... [id=vpc-0566fd74a48916695]
aws_subnet.main: Refreshing state... [id=subnet-0ce6dc1045605b580]

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  - destroy

Terraform will perform the following actions:

  # aws_subnet.main will be destroyed
  - resource "aws_subnet" "main" {
      - arn                                            = "arn:aws:ec2:us-east-2:027488552956:subnet/subnet-0ce6dc1045605b580" -> null
      - assign_ipv6_address_on_creation                = false -> null
      - availability_zone                              = "us-east-2a" -> null
      - availability_zone_id                           = "use2-az1" -> null
      - cidr_block                                     = "10.7.1.0/24" -> null
      - enable_dns64                                   = false -> null
      - enable_lni_at_device_index                     = 0 -> null
      - enable_resource_name_dns_a_record_on_launch    = false -> null
      - enable_resource_name_dns_aaaa_record_on_launch = false -> null
      - id                                             = "subnet-0ce6dc1045605b580" -> null
      - ipv6_native                                    = false -> null
      - map_customer_owned_ip_on_launch                = false -> null
      - map_public_ip_on_launch                        = false -> null
      - owner_id                                       = "027488552956" -> null
      - private_dns_hostname_type_on_launch            = "ip-name" -> null
      - tags                                           = {
          - "CostCode"    = "123"
          - "Environment" = "dev"
          - "Lab"         = "lab07"
          - "Name"        = "platform-dev-subnet"
          - "Project"     = "platform"
        } -> null
      - tags_all                                       = {
          - "CostCode"    = "123"
          - "Environment" = "dev"
          - "Lab"         = "lab07"
          - "Name"        = "platform-dev-subnet"
          - "Project"     = "platform"
        } -> null
      - vpc_id                                         = "vpc-0566fd74a48916695" -> null
        # (4 unchanged attributes hidden)
    }

  # aws_vpc.main will be destroyed
  - resource "aws_vpc" "main" {
      - arn                                  = "arn:aws:ec2:us-east-2:027488552956:vpc/vpc-0566fd74a48916695" -> null
      - assign_generated_ipv6_cidr_block     = false -> null
      - cidr_block                           = "10.7.0.0/16" -> null
      - default_network_acl_id               = "acl-0d61e3ebbebfba5ef" -> null
      - default_route_table_id               = "rtb-0d14dc99f891b020f" -> null
      - default_security_group_id            = "sg-05bca69e9de9fb9e5" -> null
      - dhcp_options_id                      = "dopt-0b3fb1f3b525c8788" -> null
      - enable_dns_hostnames                 = false -> null
      - enable_dns_support                   = true -> null
      - enable_network_address_usage_metrics = false -> null
      - id                                   = "vpc-0566fd74a48916695" -> null
      - instance_tenancy                     = "default" -> null
      - ipv6_netmask_length                  = 0 -> null
      - main_route_table_id                  = "rtb-0d14dc99f891b020f" -> null
      - owner_id                             = "027488552956" -> null
      - tags                                 = {
          - "CostCode"    = "123"
          - "Environment" = "dev"
          - "Lab"         = "lab07"
          - "Name"        = "platform-dev"
          - "Project"     = "platform"
        } -> null
      - tags_all                             = {
          - "CostCode"    = "123"
          - "Environment" = "dev"
          - "Lab"         = "lab07"
          - "Name"        = "platform-dev"
          - "Project"     = "platform"
        } -> null
        # (4 unchanged attributes hidden)
    }

Plan: 0 to add, 0 to change, 2 to destroy.

Changes to Outputs:
  - db_password        = (sensitive value) -> null
  - db_password_length = 19 -> null
  - settings           = {
      - cost_code   = "123"
      - environment = "dev"
      - project     = "platform"
    } -> null
  - subnet_id          = "subnet-0ce6dc1045605b580" -> null
  - vpc_id             = "vpc-0566fd74a48916695" -> null
  - vpc_tags           = {
      - CostCode    = "123"
      - Environment = "dev"
      - Lab         = "lab07"
      - Name        = "platform-dev"
      - Project     = "platform"
    } -> null
aws_subnet.main: Destroying... [id=subnet-0ce6dc1045605b580]
aws_subnet.main: Destruction complete after 2s
aws_vpc.main: Destroying... [id=vpc-0566fd74a48916695]
aws_vpc.main: Destruction complete after 1s

Destroy complete! Resources: 2 destroyed.
```

`Destroy complete! Resources: 2 destroyed.` Confirm the account is empty of this lab's resources:

```bash
aws ec2 describe-vpcs --region us-east-2 \
  --filters 'Name=tag:Lab,Values=lab07' --query 'Vpcs[].VpcId'
```

**Expected output**

```text
[]
```

An empty list. Now remove the local secret material:

```bash
rm -f terraform.tfvars
unset TF_VAR_db_password
```

`rm` and `unset` matter here. Leaving a real `terraform.tfvars` on disk or a secret exported in your
shell is how the value ends up somewhere you did not intend.

## Done when

- [ ] `terraform.tfvars` exists locally and matches a `.gitignore` pattern
- [ ] A plan without `TF_VAR_db_password` prompts for it, naming the variable's description
- [ ] `apply` reported `2 added` and printed `db_password = <sensitive>` with `db_password_length = 19`
- [ ] `describe-vpcs` showed `Project`, `Environment` and `CostCode` tags carrying your tfvars values
- [ ] `db_password` appears in no tag on any resource
- [ ] `terraform output -raw db_password` prints the real value
- [ ] You found the same secret in clear text inside `terraform.tfstate`
- [ ] `-var 'environment=prod'` proposed a tag change on two real resources; `TF_VAR_environment=prod` proposed nothing
- [ ] Both validation rules reject bad input with your own error messages
- [ ] `terraform destroy` reports `2 destroyed` and `describe-vpcs` returns an empty list

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| Terraform prompts `Enter a value` | A mandatory variable is unset | `export TF_VAR_db_password='not-a-real-password'` |
| `No value for required variable` | Same, in a non-interactive shell | Export the variable, or pass `-var` |
| tfvars values ignored | File is named something else, e.g. `vars.tfvars` | Rename to `terraform.tfvars` or pass `-var-file` |
| `TF_VAR_` export seems to do nothing | The same name is set in `terraform.tfvars`, which wins | Remove it from tfvars, or use `-var` |
| `Output refers to sensitive values` | An output derives from a sensitive value | Add `sensitive = true`, or wrap in `nonsensitive()` |
| `environment must be dev, test, or prod` | Validation rule tripped | Use a lowercase value from the list |
| Secret appears in a committed file | Values put in `terraform.tfvars.example` | Move them to `terraform.tfvars` |
| `InvalidSubnet.Range: not a valid subnet of the VPC` | `subnet_cidr` outside `vpc_cidr` | Keep it inside `10.7.0.0/16` |
| `VpcLimitExceeded` | Five VPCs already exist in the region | Destroy a previous lab's VPC first |
| `NoCredentialProviders` or `InvalidClientTokenId` | Credentials missing or expired | Refresh them and confirm with `aws sts get-caller-identity` |

## Cleanup

```bash
terraform destroy -auto-approve
rm -f terraform.tfvars
unset TF_VAR_db_password
```

## Next steps

- Deep dive: [docs/05-variables.md](../docs/05-variables.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab07-tfvars-secrets)
- Continue to [Lab 08 — Local State](lab08-local-state.md)
