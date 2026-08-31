# Lab 04 — Plan, Apply, and Destroy

| | |
|---|---|
| **Goal** | Run the complete Terraform lifecycle end to end against real AWS infrastructure, and see how Terraform remembers what it already built. |
| **Time** | 25–35 minutes |
| **Tier** | Basic |
| **Files** | `../labs/lab04-plan-apply-destroy/` |

## Overview

[Lab 03](lab03-first-ec2.md) ran the core commands against a real, billable server. This lab
runs the same cycle — `init`, `plan`, `apply`, `destroy` — against a **VPC**, which is real
infrastructure in your account but costs nothing to keep. You get the full lifecycle without the
meter running.

The point of the lab is what happens *between* the commands. After `apply`, Terraform writes a file
called `terraform.tfstate` recording what it created, and every later `plan` compares your
configuration against that record. That comparison is why running `plan` twice gives different
answers, and why Terraform destroys exactly what it made and nothing else.

Two resources are involved, which makes a second point. `random_string.suffix` is generated on your
machine; `aws_vpc.lifecycle` is built by AWS and uses that string in its `Name` tag. Because the VPC
depends on the string, Terraform creates the string first and destroys it last. Dependency order is
not something you declare here — Terraform infers it from the reference.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `random_string.suffix` | A six-character lowercase string, generated locally | None |
| `aws_vpc.lifecycle` | A real VPC, `10.4.0.0/16`, named from that string | None |
| 3 outputs | The generated string, the VPC ID, and the `Name` tag AWS recorded | None |
| `terraform.tfstate` | Terraform's record of what it created | None |

Two managed resources, no data sources. A VPC is free; nothing in this lab is billable.

## Before you start

- [ ] [Lab 03](lab03-first-ec2.md) completed
- [ ] AWS credentials configured for `us-east-2` (`aws sts get-caller-identity` succeeds)
- [ ] Fewer than five VPCs already in `us-east-2` — the default limit is five

## Steps

### Step 1 — Initialize the lab directory

```bash
cd terraform/labs/lab04-plan-apply-destroy
terraform init
```

**Expected output**

```text
- Finding hashicorp/random versions matching "~> 3.0"...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/random v3.9.0...
- Installed hashicorp/random v3.9.0 (signed by HashiCorp)
- Installing hashicorp/aws v5.100.0...
- Installed hashicorp/aws v5.100.0 (signed by HashiCorp)

Terraform has been successfully initialized!
```

### Step 2 — Read the configuration

```bash
cat main.tf
```

Two providers, two resources. The `random` provider runs entirely on your machine; the `aws`
provider talks to `us-east-2`. `resource "random_string" "suffix"` gives the type first, then a label
you choose — together they form the address `random_string.suffix` used in plans, in state, and in
the output blocks at the bottom of the file.

Find the line `Name = "lab04-${random_string.suffix.result}"` inside the VPC. That reference is the
only thing linking the two resources, and it is enough for Terraform to work out that the string has
to exist before the VPC can be created.

### Step 3 — Plan the change

```bash
terraform plan
```

**Expected output**

```text
PENDING CAPTURE — rerun after credentials are restored
```

`Plan: 2 to add, 0 to change, 0 to destroy.` Terraform has no record of either resource, so it
proposes creating both. The `+` symbol marks a creation, and `(known after apply)` marks a value that
does not exist until the resource does — the VPC's `id`, `arn` and `owner_id` are all in that
category, because AWS assigns them.

Nothing has been created yet. `plan` only reports, and it contacted AWS solely to check whether these
resources already exist.

### Step 4 — Apply the change

```bash
terraform apply
```

Terraform reprints the plan and waits. Type `yes` and press Enter.

**Expected output**

```text
PENDING CAPTURE — rerun after credentials are restored
```

`Apply complete! Resources: 2 added, 0 changed, 0 destroyed.`

Read the order of the two `Creation complete` lines: `random_string.suffix` finishes first, then
`aws_vpc.lifecycle`. Terraform did not guess — the VPC's `Name` tag referenced the string, so the
string had to be created first. Your string and VPC ID will differ from anyone else's.
`terraform.tfstate` now exists in the directory.

### Step 5 — Read the values back

Outputs are stored, not just printed, so you can read them back at any time.

```bash
terraform output
terraform output -raw vpc_id
```

**Expected output**

```text
PENDING CAPTURE — rerun after credentials are restored
```

### Step 6 — Confirm the VPC exists in AWS

Terraform says it built something. Ask AWS.

```bash
aws ec2 describe-vpcs --region us-east-2 \
  --filters 'Name=tag:Lab,Values=lab04' \
  --query 'Vpcs[].[VpcId,CidrBlock,Tags[?Key==`Name`].Value|[0]]' --output table
```

**Expected output**

```text
PENDING CAPTURE — rerun after credentials are restored
```

One row, and the `VpcId` matches what `terraform output -raw vpc_id` printed. The `Name` column shows
`lab04-` followed by the six letters generated on your laptop. A value that existed only in your
shell a minute ago is now metadata on a real network.

### Step 7 — Plan a second time

This is the step that matters. Nothing about your configuration changed, so run `plan` again.

```bash
terraform plan
```

**Expected output**

```text
PENDING CAPTURE — rerun after credentials are restored
```

`No changes. Your infrastructure matches the configuration.`

The first plan proposed two creations; this one proposes nothing. Two things changed in between: the
state file now exists, and the VPC now exists in AWS. Terraform read the VPC back from AWS, compared
it with the recorded state and your configuration, and found all three in agreement. `No changes` is
the normal steady state of a healthy configuration.

### Step 8 — Destroy the resources

```bash
terraform destroy
```

Terraform lists what will be removed and waits. Type `yes`.

**Expected output**

```text
PENDING CAPTURE — rerun after credentials are restored
```

`Destroy complete! Resources: 2 destroyed.`

Note the order, which is the reverse of Step 4: `aws_vpc.lifecycle` is destroyed first, then
`random_string.suffix`. Terraform walks the dependency graph backwards on destroy, because a resource
cannot be removed while something else still depends on it.

### Step 9 — Confirm nothing is left

```bash
terraform state list
aws ec2 describe-vpcs --region us-east-2 \
  --filters 'Name=tag:Lab,Values=lab04' --query 'Vpcs[].VpcId'
```

**Expected output**

```text
PENDING CAPTURE — rerun after credentials are restored
```

`state list` prints nothing and `describe-vpcs` returns an empty list. Both checks matter: the first
says Terraform manages nothing here, the second says AWS is holding nothing either. A fresh `plan`
would again propose creating both resources. [Lab 08](lab08-local-state.md) examines state.

## Done when

- [ ] The first `plan` showed `2 to add`
- [ ] `apply` printed a value for `generated_value` and a `vpc-` ID for `vpc_id`
- [ ] `random_string.suffix` was created before `aws_vpc.lifecycle`, without you declaring an order
- [ ] `aws ec2 describe-vpcs` found the VPC with a `Name` tag containing your generated suffix
- [ ] The second `plan` reported `No changes`
- [ ] `destroy` reported `2 destroyed`, removing the VPC before the string
- [ ] `terraform state list` prints nothing and `describe-vpcs` returns an empty list

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `Could not load plugin` | `init` not run in this directory | Run `terraform init` |
| Second plan still shows `2 to add` | The apply was not confirmed with `yes` | Re-run `terraform apply` |
| `VpcLimitExceeded` | Five VPCs already exist in `us-east-2` | Destroy another lab's VPC, then retry |
| `NoCredentialProviders` or `InvalidClientTokenId` | Credentials missing or expired | Refresh them and confirm with `aws sts get-caller-identity` |
| `UnauthorizedOperation` on `CreateVpc` | Credentials lack EC2 permissions | Use the account from Lab 00 |
| `Error asking for approval` | Terminal cannot accept input | Use `terraform apply -auto-approve` |
| A different string each apply | Expected — the value is random | No action needed |
| `Error acquiring the state lock` | Another Terraform process is running | Wait for it to finish, then retry |
| `destroy` reports `0 destroyed` | Already destroyed | Confirm with `terraform state list` |

## Cleanup

```bash
terraform destroy
```

The state file is left behind deliberately so you can inspect it. Removing it is optional, and
safe only once `destroy` has finished:

```bash
rm -f terraform.tfstate terraform.tfstate.backup
```

## Next steps

- Deep dive: [The core workflow](../docs/03-workflow.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab04-plan-apply-destroy)
- Continue to [Lab 05 — Format and Validate](lab05-fmt-validate.md)
