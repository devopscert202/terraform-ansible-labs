# Lab 08 — Local State

| | |
|---|---|
| **Goal** | Inspect the local `terraform.tfstate` file, list and show resources with the state commands, and confirm that state stores secrets as plain text. |
| **Time** | 40–50 minutes |
| **Tier** | Intermediate |
| **Files** | `terraform/labs/lab08-local-state/` |

## Overview

Every `apply` you have run wrote a file called `terraform.tfstate`. **State** is Terraform's record
of what it created: one entry per resource, holding the real ID AWS handed back and every attribute
value. It is how Terraform knows on the next run whether to create, change, or leave a resource
alone. Without state, Terraform would create a duplicate every time.

Because there is no `backend` block in this configuration, state is a JSON file sitting in the lab
directory. That is fine for one person on one laptop and wrong for a team, for two reasons you will
prove here: the file is easy to lose, and anything sensitive inside it is in plain text.
[Lab 17](lab17-s3-backend.md) fixes both by moving state to S3.

Two of the three resources here are generated locally, and the third is a real VPC. That mix is
deliberate. The `random_password` proves state stores secrets in the clear. The VPC proves the other
half of the lesson: state is the *only* local record that a real thing exists in a real account.
Lose the file and the VPC does not disappear — it becomes an orphan nothing manages, and the next
`apply` builds a second one beside it.

A VPC costs nothing, but it is real, so this lab needs AWS credentials. The generated values differ
on every run, so your pet name, password and VPC ID will not match the examples below.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `random_pet.server` | A generated name, used as the VPC's `Name` tag | Free |
| `random_password.db` | A generated 16-character secret | Free |
| `aws_vpc.main` | A real VPC, `10.8.0.0/16`, whose ID state must remember | Free |
| `terraform.tfstate` | The local state file you will inspect | Free |

Three managed resources, no data sources.

## Before you start

- [ ] Lab 07 completed ([lab07-tfvars-secrets.md](lab07-tfvars-secrets.md)), where you saw that
  `sensitive = true` hides a value on screen but does not encrypt it
- [ ] `python3` available, for reading the state file's JSON structure in Step 12
- [ ] AWS credentials configured for `us-east-2` (`aws sts get-caller-identity` succeeds)
- [ ] Working directory: `../labs/lab08-local-state/`

## Steps

### Step 1 — Confirm no state exists yet

```bash
cd terraform/labs/lab08-local-state
ls
```

**Expected output**

```text
main.tf
outputs.tf
```

Two files, no state. Terraform creates the state file on the first `apply`, not on `init`.

### Step 2 — Note the absence of a backend block

```bash
head -15 main.tf
```

**Expected output**

```text
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# There is no backend block, so Terraform writes state to ./terraform.tfstate.
```

A `backend` block tells Terraform where to keep state. There is none here, which means the default:
a local file named `terraform.tfstate` in the current directory.

### Step 3 — Initialize

```bash
terraform init
```

**Expected output** *(trimmed)*

```text
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Finding hashicorp/random versions matching "~> 3.0"...
- Installing hashicorp/aws v5.100.0...
- Installed hashicorp/aws v5.100.0 (signed by HashiCorp)
- Installing hashicorp/random v3.9.0...
- Installed hashicorp/random v3.9.0 (signed by HashiCorp)

Terraform has been successfully initialized!
```

### Step 4 — Apply

```bash
terraform apply -auto-approve
```

**Expected output**

```text

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # aws_vpc.main will be created
  + resource "aws_vpc" "main" {
      + arn                                  = (known after apply)
      + cidr_block                           = "10.8.0.0/16"
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
      + tags                                 = (known after apply)
      + tags_all                             = (known after apply)
    }

  # random_password.db will be created
  + resource "random_password" "db" {
      + bcrypt_hash = (sensitive value)
      + id          = (known after apply)
      + length      = 16
      + lower       = true
      + min_lower   = 0
      + min_numeric = 0
      + min_special = 0
      + min_upper   = 0
      + number      = true
      + numeric     = true
      + result      = (sensitive value)
      + special     = false
      + upper       = true
    }

  # random_pet.server will be created
  + resource "random_pet" "server" {
      + id        = (known after apply)
      + length    = 2
      + prefix    = "lab08"
      + separator = "-"
    }

Plan: 3 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + db_password = (sensitive value)
  + server_name = (known after apply)
  + vpc_id      = (known after apply)
random_pet.server: Creating...
random_password.db: Creating...
random_pet.server: Creation complete after 0s [id=lab08-legible-liger]
random_password.db: Creation complete after 0s [id=none]
aws_vpc.main: Creating...
aws_vpc.main: Creation complete after 4s [id=vpc-0156a9423efd5285a]

Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

Outputs:

db_password = <sensitive>
server_name = "lab08-legible-liger"
vpc_id = "vpc-0156a9423efd5285a"
```

`Apply complete! Resources: 3 added, 0 changed, 0 destroyed.`

`random_password.db` reports `id=none` on purpose — that provider does not expose a meaningful ID.
The value it generated is in the `result` attribute, which you will find in Step 13.

`aws_vpc.main` reports a real ID of the form `vpc-` followed by seventeen hex characters. AWS
generated that ID, not Terraform, and the state file is now the only place on your machine that
records it.

### Step 5 — Find the state file

```bash
ls -l terraform.tfstate
```

**Expected output**

```text
-rw-r--r--@ 1 kpakkiriswamy  wheel  3879 31 Aug 11:48 terraform.tfstate
```

The file now exists, several kilobytes of JSON. Never edit it by hand — hand edits are how you get a
state file that disagrees with reality.

### Step 6 — List what state is tracking

```bash
terraform state list
```

**Expected output**

```text
aws_vpc.main
random_password.db
random_pet.server
```

Each line is a **resource address** — the `type.name` pair you wrote in your configuration.
Addresses are how you refer to one specific resource in every state command.

### Step 7 — Show a real resource's recorded attributes

```bash
terraform state show random_pet.server
terraform state show aws_vpc.main
```

**Expected output**

```text
# random_pet.server:
resource "random_pet" "server" {
    id        = "lab08-legible-liger"
    length    = 2
    prefix    = "lab08"
    separator = "-"
}
# aws_vpc.main:
resource "aws_vpc" "main" {
    arn                                  = "arn:aws:ec2:us-east-2:027488552956:vpc/vpc-0156a9423efd5285a"
    assign_generated_ipv6_cidr_block     = false
    cidr_block                           = "10.8.0.0/16"
    default_network_acl_id               = "acl-0f5377ef0cf2b5926"
    default_route_table_id               = "rtb-0816b3e8a9b597882"
    default_security_group_id            = "sg-0677be06982cac0fd"
    dhcp_options_id                      = "dopt-0b3fb1f3b525c8788"
    enable_dns_hostnames                 = false
    enable_dns_support                   = true
    enable_network_address_usage_metrics = false
    id                                   = "vpc-0156a9423efd5285a"
    instance_tenancy                     = "default"
    ipv6_association_id                  = null
    ipv6_cidr_block                      = null
    ipv6_cidr_block_network_border_group = null
    ipv6_ipam_pool_id                    = null
    ipv6_netmask_length                  = 0
    main_route_table_id                  = "rtb-0816b3e8a9b597882"
    owner_id                             = "027488552956"
    tags                                 = {
        "Lab"  = "lab08"
        "Name" = "lab08-legible-liger"
    }
    tags_all                             = {
        "Lab"  = "lab08"
        "Name" = "lab08-legible-liger"
    }
}
```

For `random_pet.server` you wrote `length` and `prefix`; Terraform recorded those plus `id` and
`separator`, which it learned from the provider.

`aws_vpc.main` is the more instructive one. You wrote two arguments — `cidr_block` and
`enable_dns_support` — and state holds roughly twenty, including `id`, `arn`, `owner_id`,
`default_route_table_id` and `main_route_table_id`. Every one of those came back from AWS. That full
picture is what makes the next `plan` accurate: Terraform compares your two arguments against the
recorded values and can tell you nothing has drifted.

### Step 8 — Confirm the recorded ID matches AWS

```bash
terraform output -raw vpc_id
aws ec2 describe-vpcs --region us-east-2 \
  --filters 'Name=tag:Lab,Values=lab08' --query 'Vpcs[].VpcId' --output text
```

**Expected output**

```text
vpc-0156a9423efd5285a
vpc-0156a9423efd5285a
```

The same `vpc-` ID printed twice: once from the state file on your laptop, once from AWS. State is
not a cache or a log. It is the mapping between your configuration and that ID, and it is the only
copy you have.

### Step 9 — Show the resource that holds a secret

```bash
terraform state show random_password.db
```

**Expected output**

```text
# random_password.db:
resource "random_password" "db" {
    bcrypt_hash = (sensitive value)
    id          = "none"
    length      = 16
    lower       = true
    min_lower   = 0
    min_numeric = 0
    min_special = 0
    min_upper   = 0
    number      = true
    numeric     = true
    result      = (sensitive value)
    special     = false
    upper       = true
}
```

The provider marked `result` and `bcrypt_hash` as sensitive, so the CLI prints `(sensitive value)`.
Remember this screen — Step 13 reads the same attribute from the file underneath it.

### Step 10 — Show the whole state at once

```bash
terraform show
```

**Expected output**

```text
# aws_vpc.main:
resource "aws_vpc" "main" {
    arn                                  = "arn:aws:ec2:us-east-2:027488552956:vpc/vpc-0156a9423efd5285a"
    assign_generated_ipv6_cidr_block     = false
    cidr_block                           = "10.8.0.0/16"
    default_network_acl_id               = "acl-0f5377ef0cf2b5926"
    default_route_table_id               = "rtb-0816b3e8a9b597882"
    default_security_group_id            = "sg-0677be06982cac0fd"
    dhcp_options_id                      = "dopt-0b3fb1f3b525c8788"
    enable_dns_hostnames                 = false
    enable_dns_support                   = true
    enable_network_address_usage_metrics = false
    id                                   = "vpc-0156a9423efd5285a"
    instance_tenancy                     = "default"
    ipv6_association_id                  = null
    ipv6_cidr_block                      = null
    ipv6_cidr_block_network_border_group = null
    ipv6_ipam_pool_id                    = null
    ipv6_netmask_length                  = 0
    main_route_table_id                  = "rtb-0816b3e8a9b597882"
    owner_id                             = "027488552956"
    tags                                 = {
        "Lab"  = "lab08"
        "Name" = "lab08-legible-liger"
    }
    tags_all                             = {
        "Lab"  = "lab08"
        "Name" = "lab08-legible-liger"
    }
}

# random_password.db:
resource "random_password" "db" {
    bcrypt_hash = (sensitive value)
    id          = "none"
    length      = 16
    lower       = true
    min_lower   = 0
    min_numeric = 0
    min_special = 0
    min_upper   = 0
    number      = true
    numeric     = true
    result      = (sensitive value)
    special     = false
    upper       = true
}

# random_pet.server:
resource "random_pet" "server" {
    id        = "lab08-legible-liger"
    length    = 2
    prefix    = "lab08"
    separator = "-"
}


Outputs:

db_password = (sensitive value)
server_name = "lab08-legible-liger"
vpc_id = "vpc-0156a9423efd5285a"
```

`terraform show` prints every tracked resource — all three, `aws_vpc.main` included — and then every
output. Use it to see the whole picture; use `state show` when you want one resource.

### Step 11 — Read outputs, and watch the redaction come off

```bash
terraform output
terraform output db_password
terraform output -raw db_password
```

**Expected output**

```text
db_password = <sensitive>
server_name = "lab08-legible-liger"
vpc_id = "vpc-0156a9423efd5285a"
"Znl2Yw6NGQKb9jSa"
Znl2Yw6NGQKb9jSa
```

Three different renderings of the same stored value: `db_password = <sensitive>` when you list all
outputs, the quoted value when you name it, and the bare value with `-raw`. Listing all outputs redacts it. Asking for it
by name prints it with quotes, and `-raw` prints it bare. Redaction is a guard against accidental
display, not a permission boundary — if you ask directly, you get the secret.

### Step 12 — Look at the state file's structure

```bash
python3 -c "import json; d=json.load(open('terraform.tfstate')); print('version', d['version']); print('serial', d['serial']); print('resources', [r['type']+'.'+r['name'] for r in d['resources']])"
```

**Expected output**

```text
version 4
serial 4
resources ['aws_vpc.main', 'random_password.db', 'random_pet.server']
```

`version` is `4`, and `resources` lists all three addresses including `aws_vpc.main`.

State is ordinary JSON with a documented shape. `version` is the state format version, `serial`
increments on every write, and `resources` is the list you saw in Step 6. Terraform uses `serial`
and a `lineage` field to detect that two people have written the same state — the problem a remote
backend with locking exists to prevent.

### Step 13 — Read the secret straight out of the state file

```bash
grep -o '"result": "[^"]*"' terraform.tfstate
```

**Expected output**

```text
"result": "Znl2Yw6NGQKb9jSa"
```

One line, `"result": "<the generated password>"`. This is the lesson the whole lab exists for. Step 9 showed this attribute as `(sensitive value)`;
the redaction is a display convenience in the CLI. In the file, the generated password is stored in
clear text. Anyone who can read the file can read the secret, which is why a local state file must
never be committed to git and why [Lab 17](lab17-s3-backend.md) moves state into encrypted remote
storage.

### Step 14 — Prove state prevents duplicate creation

```bash
terraform plan
```

**Expected output**

```text
random_pet.server: Refreshing state... [id=lab08-legible-liger]
random_password.db: Refreshing state... [id=none]
aws_vpc.main: Refreshing state... [id=vpc-0156a9423efd5285a]

No changes. Your infrastructure matches the configuration.

Terraform has compared your real infrastructure against your configuration
and found no differences, so no changes are needed.
```

`No changes. Your infrastructure matches the configuration.` Terraform refreshed the VPC against
AWS, compared what came back with the configuration, found them identical, and proposed nothing.

Now consider the failure mode. Delete `terraform.tfstate` and this same plan proposes creating all
three resources again. For the two `random_` resources that is harmless. For the VPC it is not: the
existing VPC stays in your account, unmanaged and unnamed in any configuration, and you get a second
one. That is what makes losing a state file a real incident rather than an inconvenience, and it is
the reason the next few labs move state somewhere durable.

### Step 15 — Destroy, and see what state looks like afterwards

```bash
terraform destroy -auto-approve
ls
terraform state list
```

**Expected output**

```text
random_pet.server: Refreshing state... [id=lab08-legible-liger]
random_password.db: Refreshing state... [id=none]
aws_vpc.main: Refreshing state... [id=vpc-0156a9423efd5285a]

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  - destroy

Terraform will perform the following actions:

  # aws_vpc.main will be destroyed
  - resource "aws_vpc" "main" {
      - arn                                  = "arn:aws:ec2:us-east-2:027488552956:vpc/vpc-0156a9423efd5285a" -> null
      - assign_generated_ipv6_cidr_block     = false -> null
      - cidr_block                           = "10.8.0.0/16" -> null
      - default_network_acl_id               = "acl-0f5377ef0cf2b5926" -> null
      - default_route_table_id               = "rtb-0816b3e8a9b597882" -> null
      - default_security_group_id            = "sg-0677be06982cac0fd" -> null
      - dhcp_options_id                      = "dopt-0b3fb1f3b525c8788" -> null
      - enable_dns_hostnames                 = false -> null
      - enable_dns_support                   = true -> null
      - enable_network_address_usage_metrics = false -> null
      - id                                   = "vpc-0156a9423efd5285a" -> null
      - instance_tenancy                     = "default" -> null
      - ipv6_netmask_length                  = 0 -> null
      - main_route_table_id                  = "rtb-0816b3e8a9b597882" -> null
      - owner_id                             = "027488552956" -> null
      - tags                                 = {
          - "Lab"  = "lab08"
          - "Name" = "lab08-legible-liger"
        } -> null
      - tags_all                             = {
          - "Lab"  = "lab08"
          - "Name" = "lab08-legible-liger"
        } -> null
        # (4 unchanged attributes hidden)
    }

  # random_password.db will be destroyed
  - resource "random_password" "db" {
      - bcrypt_hash = (sensitive value) -> null
      - id          = "none" -> null
      - length      = 16 -> null
      - lower       = true -> null
      - min_lower   = 0 -> null
      - min_numeric = 0 -> null
      - min_special = 0 -> null
      - min_upper   = 0 -> null
      - number      = true -> null
      - numeric     = true -> null
      - result      = (sensitive value) -> null
      - special     = false -> null
      - upper       = true -> null
    }

  # random_pet.server will be destroyed
  - resource "random_pet" "server" {
      - id        = "lab08-legible-liger" -> null
      - length    = 2 -> null
      - prefix    = "lab08" -> null
      - separator = "-" -> null
    }

Plan: 0 to add, 0 to change, 3 to destroy.

Changes to Outputs:
  - db_password = (sensitive value) -> null
  - server_name = "lab08-legible-liger" -> null
  - vpc_id      = "vpc-0156a9423efd5285a" -> null
random_password.db: Destroying... [id=none]
random_password.db: Destruction complete after 0s
aws_vpc.main: Destroying... [id=vpc-0156a9423efd5285a]
aws_vpc.main: Destruction complete after 2s
random_pet.server: Destroying... [id=lab08-legible-liger]
random_pet.server: Destruction complete after 0s

Destroy complete! Resources: 3 destroyed.
main.tf
outputs.tf
terraform.tfstate
terraform.tfstate.backup
```

`Destroy complete! Resources: 3 destroyed.` Then `ls` shows `main.tf`, `outputs.tf`,
`terraform.tfstate` and `terraform.tfstate.backup`, and `terraform state list` prints nothing,
because state now tracks zero resources. Note that `terraform.tfstate` was not deleted — it still
exists, emptied — and a `terraform.tfstate.backup` now holds the previous version. Both are
gitignored in this repository.

Confirm the VPC is really gone rather than merely forgotten:

```bash
aws ec2 describe-vpcs --region us-east-2 \
  --filters 'Name=tag:Lab,Values=lab08' --query 'Vpcs[].VpcId'
```

**Expected output**

```text
[]
```

An empty list.

## Done when

- [ ] `terraform.tfstate` exists after `apply` and did not exist before
- [ ] `apply` reported `3 added`
- [ ] `terraform state list` shows all three resource addresses
- [ ] `terraform state show aws_vpc.main` prints roughly twenty attributes you never wrote
- [ ] The `vpc_id` output and `aws ec2 describe-vpcs` print the same ID
- [ ] `state show random_password.db` shows `result = (sensitive value)`
- [ ] `terraform output -raw db_password` prints the secret in the clear
- [ ] You located that same password in plain text inside `terraform.tfstate`
- [ ] `terraform plan` reports `No changes`
- [ ] You can explain why deleting the state file is worse for the VPC than for the two `random_` resources
- [ ] After `destroy`, `state list` is empty, the state file remains, and `describe-vpcs` returns an empty list

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `No state file was found` | `apply` has not run yet in this directory | Run `terraform apply` |
| `Invalid resource address` | Typo in the address | Copy the exact line from `terraform state list` |
| `grep` finds nothing | Apply did not complete, or you are in the wrong directory | `pwd`, then `ls -l terraform.tfstate` |
| `KeyError: 'resources'` in Step 12 | State has no resources yet, or was destroyed first | Re-run `terraform apply` before Step 12 |
| Plan wants to create both resources again | State file deleted or you are in another directory | `pwd`, and confirm the state file is present |
| `Provider configuration not present` | `.terraform` cache removed | Run `terraform init` again |
| `VpcLimitExceeded` | Five VPCs already exist in the region | Destroy a previous lab's VPC first |
| `NoCredentialProviders` or `InvalidClientTokenId` | Credentials missing or expired | Refresh them and confirm with `aws sts get-caller-identity` |

## Cleanup

```bash
terraform destroy -auto-approve
```

## Next steps

- Deep dive: [docs/06-state.md](../docs/06-state.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab08-local-state)
- Continue to [Lab 09 — Modules](lab09-modules.md)
