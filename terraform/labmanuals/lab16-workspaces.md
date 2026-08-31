# Lab 16 — Workspaces

| | |
|---|---|
| **Goal** | Keep two independent copies of the same configuration side by side, each with its own state, and read the active workspace name from inside the code. |
| **Time** | 25–30 minutes |
| **Tier** | Advanced |
| **Files** | `terraform/labs/lab16-workspaces/` |

## Overview

Every Terraform directory you have used so far had exactly one state file, so applying the
configuration twice with different values would overwrite the first result. A **workspace** is a
named, separate state file for the same configuration directory. Switch workspace and Terraform
forgets the other workspace's resources entirely — the code is shared, the state is not.

Every directory starts with one workspace called `default`, which is why you have never had to
think about this. This lab creates a second workspace, applies in both, and reads the built-in
`terraform.workspace` value so resource names and tags can vary per environment.

Workspaces are lightweight: they give you separate state and nothing else — no separate AWS
account, no separate credentials, no approval gate. That limitation motivates the next two labs,
which use separate state keys instead.

Reading a workspace name back out of an output only proves Terraform knows which workspace is
active. So this lab creates a real VPC per workspace, at a different CIDR chosen by workspace name.
By Step 10 there are **two VPCs in your account at the same time**, from one configuration
directory, and neither state file knows the other exists. That is the isolation claim, tested
against AWS rather than asserted.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `terraform_data.workspace` | Stores a label map built from the active workspace name | Free |
| `aws_vpc.env` | A real VPC per workspace: `10.16.0.0/16` in `default`, `10.17.0.0/16` in `dev` | Free |
| Outputs `workspace`, `labels` | The active workspace name and the label map | Free |
| Outputs `vpc_id`, `vpc_cidr`, `vpc_name` | The VPC belonging to the active workspace only | Free |

One managed resource per workspace, plus the placeholder — so **two** resources per workspace and
four in total once both workspaces are applied.

## Before you start

- [ ] [Lab 15 — remote-exec provisioner](lab15-remote-exec-provisioner.md) completed
- [ ] Terraform 1.5.0 or newer (`terraform version`)
- [ ] Read the state model notes in [../docs/12-workspaces.md](../docs/12-workspaces.md)
- [ ] AWS credentials configured for `us-east-2` (`aws sts get-caller-identity` succeeds)
- [ ] Room for two more VPCs in `us-east-2` — this lab holds two at once, and the default limit is
  five per region

A VPC costs nothing, but the two this lab creates are real and stay in place until after
[Lab 20](lab20-remote-state-consumer.md). See the Cleanup section.

## Steps

### Step 1 — Move into the lab directory and read the workspace reference

`terraform.workspace` is a built-in value, not a variable. It always holds the name of the active
workspace, so you never declare it and it needs no default.

```bash
cd terraform/labs/lab16-workspaces
cat main.tf
```

**Expected output**

**Expected output** *(trimmed to the parts that matter)*

```text
variable "workspace_cidrs" {
  type        = map(string)
  description = "CIDR per workspace name. lookup() falls back for any other name."
  default = {
    default = "10.16.0.0/16"
    dev     = "10.17.0.0/16"
  }
}

locals {
  environment = terraform.workspace
  labels      = { environment = terraform.workspace, managed_by = "terraform" }

  name     = "lab16-${terraform.workspace}"
  vpc_cidr = lookup(var.workspace_cidrs, terraform.workspace, "10.18.0.0/16")
}

resource "terraform_data" "workspace" { input = local.labels }

# A real VPC per workspace. Two workspaces, two states, two VPCs in the account
# at the same time — which is the proof that workspace state really is separate.
resource "aws_vpc" "env" {
  cidr_block         = local.vpc_cidr
  enable_dns_support = true

  tags = {
    Lab         = "lab16"
    Name        = local.name
    Environment = terraform.workspace
  }
}
```

`terraform.workspace` appears four times and does four different jobs: it names the resource, tags
it, picks its CIDR through `lookup()`, and lands in the label map. Nothing else in the file changes
between workspaces — a single string is the whole difference between the two environments.

`lookup(map, key, fallback)` returns the fallback when the key is absent, so applying in a workspace
called anything other than `default` or `dev` still gets a valid, non-overlapping CIDR.

### Step 2 — Initialize

```bash
terraform init
```

**Expected output** *(trimmed)*

```text
Initializing provider plugins...
- terraform.io/builtin/terraform is built in to Terraform
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installed hashicorp/aws v5.100.0 (signed by HashiCorp)

Terraform has been successfully initialized!
```

### Step 3 — Validate the configuration

```bash
terraform validate
```

**Expected output**

```text
Success! The configuration is valid.
```

### Step 4 — Confirm which workspace you are in

Every directory starts in `default`. The asterisk in `workspace list` marks the active one.

```bash
terraform workspace show
terraform workspace list
```

**Expected output**

```text
default
* default
```

### Step 5 — Apply in the default workspace

```bash
terraform apply -auto-approve
```

**Expected output**

```text

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # aws_vpc.env will be created
  + resource "aws_vpc" "env" {
      + arn                                  = (known after apply)
      + cidr_block                           = "10.16.0.0/16"
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
          + "Environment" = "default"
          + "Lab"         = "lab16"
          + "Name"        = "lab16-default"
        }
      + tags_all                             = {
          + "Environment" = "default"
          + "Lab"         = "lab16"
          + "Name"        = "lab16-default"
        }
    }

  # terraform_data.workspace will be created
  + resource "terraform_data" "workspace" {
      + id     = (known after apply)
      + input  = {
          + environment = "default"
          + managed_by  = "terraform"
        }
      + output = (known after apply)
    }

Plan: 2 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + labels    = (known after apply)
  + vpc_cidr  = "10.16.0.0/16"
  + vpc_id    = (known after apply)
  + vpc_name  = "lab16-default"
  + workspace = "default"
terraform_data.workspace: Creating...
terraform_data.workspace: Creation complete after 0s [id=5fa92df3-2cc6-f2b1-357e-cf32062d8a7e]
aws_vpc.env: Creating...
aws_vpc.env: Creation complete after 4s [id=vpc-0efb0b80941b4805e]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

labels = {
  "environment" = "default"
  "managed_by" = "terraform"
}
vpc_cidr = "10.16.0.0/16"
vpc_id = "vpc-0efb0b80941b4805e"
vpc_name = "lab16-default"
workspace = "default"
```

`Plan: 2 to add, 0 to change, 0 to destroy.` then `Apply complete! Resources: 2 added, 0 changed, 0
destroyed.`

`terraform.workspace` resolved to `default`, so that is what landed in the label map, in the VPC's
`Environment` tag, and in `vpc_name` as `lab16-default`. `vpc_cidr` is `10.16.0.0/16`, the value
`lookup()` found under the `default` key.

### Step 6 — Create and switch to a second workspace

`workspace new` creates the workspace and switches to it in one step.

```bash
terraform workspace new dev
```

**Expected output**

```text
Created and switched to workspace "dev"!

You're now on a new, empty workspace. Workspaces isolate their state,
so if you run "terraform plan" Terraform will not see any existing state
for this configuration.
```

### Step 7 — Prove the new workspace's state is empty

You applied a resource moments ago, yet this workspace cannot see it. That is the isolation the
whole feature exists to provide.

```bash
terraform state list
```

**Expected output**

```text
No state file was found!

State management commands require a state file. Run this command
in a directory where Terraform has been run or use the -state flag
to point the command to a specific state location.
```

### Step 8 — Apply in the new workspace

The command is identical to step 5, but it acts on different state and produces a different
result — which is why it is a separate operation, not a repeat.

```bash
terraform apply -auto-approve
```

**Expected output**

```text

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # aws_vpc.env will be created
  + resource "aws_vpc" "env" {
      + arn                                  = (known after apply)
      + cidr_block                           = "10.17.0.0/16"
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
          + "Environment" = "dev"
          + "Lab"         = "lab16"
          + "Name"        = "lab16-dev"
        }
      + tags_all                             = {
          + "Environment" = "dev"
          + "Lab"         = "lab16"
          + "Name"        = "lab16-dev"
        }
    }

  # terraform_data.workspace will be created
  + resource "terraform_data" "workspace" {
      + id     = (known after apply)
      + input  = {
          + environment = "dev"
          + managed_by  = "terraform"
        }
      + output = (known after apply)
    }

Plan: 2 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + labels    = (known after apply)
  + vpc_cidr  = "10.17.0.0/16"
  + vpc_id    = (known after apply)
  + vpc_name  = "lab16-dev"
  + workspace = "dev"
terraform_data.workspace: Creating...
terraform_data.workspace: Creation complete after 0s [id=a754b276-cc93-5b57-72d8-b539c196df1d]
aws_vpc.env: Creating...
aws_vpc.env: Creation complete after 4s [id=vpc-090e81535ff58fe9c]

Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

labels = {
  "environment" = "dev"
  "managed_by" = "terraform"
}
vpc_cidr = "10.17.0.0/16"
vpc_id = "vpc-090e81535ff58fe9c"
vpc_name = "lab16-dev"
workspace = "dev"
```

`Plan: 2 to add, 0 to change, 0 to destroy.` again, with `environment = "dev"`, `vpc_name` of
`lab16-dev` and `vpc_cidr` of `10.17.0.0/16`.

Read that plan carefully. Terraform proposed **creating** a VPC, not modifying the one it created in
Step 5. This workspace's state is empty, so as far as Terraform is concerned no VPC exists. The two
workspaces do not know about each other.

### Step 9 — Prove both VPCs exist in AWS at once

This is the step the lab exists for. Ask AWS, not Terraform.

```bash
aws ec2 describe-vpcs --region us-east-2 \
  --filters 'Name=tag:Lab,Values=lab16' \
  --query 'Vpcs[].[VpcId,CidrBlock,Tags[?Key==`Name`].Value|[0]]' --output table
```

**Expected output**

```text
------------------------------------------------------------
|                       DescribeVpcs                       |
+-----------------------+----------------+-----------------+
|  vpc-090e81535ff58fe9c|  10.17.0.0/16  |  lab16-dev      |
|  vpc-0efb0b80941b4805e|  10.16.0.0/16  |  lab16-default  |
+-----------------------+----------------+-----------------+
```

Two rows — `lab16-dev` at `10.17.0.0/16` and `lab16-default` at `10.16.0.0/16`; AWS returns them in
its own order, not the order you applied them. One configuration
directory, one `main.tf`, two live networks. Neither state file mentions the other's VPC — run
`terraform state list` in either workspace and you will see exactly one `aws_vpc.env`.

That is the whole feature, and it is also the whole limitation. Both VPCs are in the *same* account
under the *same* credentials, because a workspace separates state and nothing else. If `dev` is
meant to be a different account, workspaces cannot give you that.

### Step 10 — List the workspaces

```bash
terraform workspace list
```

**Expected output**

```text
  default
* dev
```

### Step 11 — Find the state files on disk

This layout matters in lab 20, where another module reads one of these files directly by path.

```bash
find . -name '*.tfstate' -not -path './.terraform/*'
```

**Expected output**

```text
./terraform.tfstate
./terraform.tfstate.d/dev/terraform.tfstate
```

The `default` workspace keeps the plain `terraform.tfstate`; every named workspace gets its own
file under `terraform.tfstate.d/<name>/`.

### Step 12 — Switch back and confirm the first workspace survived

```bash
terraform workspace select default
terraform output
```

**Expected output**

```text
Switched to workspace "default".
labels = {
  "environment" = "default"
  "managed_by" = "terraform"
}
vpc_cidr = "10.16.0.0/16"
vpc_id = "vpc-0efb0b80941b4805e"
vpc_name = "lab16-default"
workspace = "default"
```

`Switched to workspace "default".` then the `default` workspace's outputs: `environment = "default"`,
`vpc_name = "lab16-default"`, `vpc_cidr = "10.16.0.0/16"`, and the same `vpc_id` you saw in Step 5.

Switching workspaces changed nothing on either side. No VPC was created, destroyed or modified —
Terraform simply started reading a different state file, and both VPCs are still running.

## Done when

- [ ] `terraform workspace list` shows both `default` and `dev`
- [ ] `terraform state list` in the fresh `dev` workspace reported no state file
- [ ] Each `apply` reported `2 added` — Terraform created a VPC in `dev` rather than modifying the one from `default`
- [ ] The `labels` output read `environment = "dev"` in `dev` and `"default"` in `default`
- [ ] `aws ec2 describe-vpcs` showed **two** VPCs, `lab16-default` and `lab16-dev`, at different CIDRs
- [ ] `terraform state list` in either workspace shows exactly one `aws_vpc.env`, never two
- [ ] Both state files exist at the paths shown in step 11
- [ ] Switching workspaces changed nothing in AWS
- [ ] You can state one thing workspaces isolate and one thing they do not
- [ ] You have **not** run the cleanup commands — lab 20 needs both state files

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `Workspace "dev" already exists` | The workspace was created in an earlier attempt | Use `terraform workspace select dev` instead of `new` |
| Plan shows resources you thought you destroyed | You are in a different workspace than you expect | Run `terraform workspace show` before every plan |
| `Currently selected workspace "dev" does not exist` | State directory was deleted while `dev` was active | `terraform workspace select default`, then recreate `dev` |
| `terraform output` prints nothing | The active workspace has never been applied | Apply in that workspace first |
| `Cannot delete the currently selected workspace` | Tried to delete the active workspace | Select `default` first, then `terraform workspace delete dev` |
| `Workspace is not empty` on delete | The workspace still has resources in state | Destroy in that workspace before deleting it |
| `VpcLimitExceeded` on the second apply | Four or more VPCs already exist in `us-east-2` | Destroy another lab's VPC, then retry |
| `InvalidVpc.Range` or overlapping CIDR | `workspace_cidrs` edited so two workspaces share a range | Give every workspace a distinct `/16` |
| `NoCredentialProviders` or `InvalidClientTokenId` | Credentials missing or expired | Refresh them and confirm with `aws sts get-caller-identity` |

## Cleanup

**Do not run this yet.** [Lab 20](lab20-remote-state-consumer.md) reads both state files this lab
just created — the `default` one in its step 2 and the `dev` one in its step 9. Destroying here
makes lab 20 fail with `Failed to read state file`.

The two VPCs are free, so leaving them in place costs nothing — but they are real, they count against
the five-VPC limit in `us-east-2`, and they must not be forgotten. Go straight to Lab 20, then return
here. Each workspace must be destroyed separately: destroying one leaves the other untouched, which
is the same isolation you proved in Step 9.

```bash
terraform workspace select dev
terraform destroy -auto-approve
terraform workspace select default
terraform destroy -auto-approve
terraform workspace delete dev
```

Then confirm both VPCs are gone:

```bash
aws ec2 describe-vpcs --region us-east-2 \
  --filters 'Name=tag:Lab,Values=lab16' --query 'Vpcs[].VpcId'
```

**Expected output**

```text
[]
```

An empty list. If one VPC remains, you destroyed only one workspace — reread the two `select` lines
above.

## Next steps

- Deep dive: [../docs/12-workspaces.md](../docs/12-workspaces.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab16-workspaces)
- Continue to [Lab 17 — S3 backend](lab17-s3-backend.md)
