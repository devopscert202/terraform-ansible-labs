# Lab 03 — Your First EC2 Instance

| | |
|---|---|
| **Goal** | Create one real virtual server in AWS from a Terraform file, confirm it exists, then destroy it. |
| **Time** | 30–40 minutes |
| **Tier** | Basic |
| **Files** | `../labs/lab03-first-ec2/` |

## Overview

In [Lab 02](lab02-console-vpc.md) you clicked through the console. Now you describe a server in
a file and let Terraform build it. An **EC2 instance** is a virtual machine running in AWS,
charged by the second while it exists.

This lab introduces the two block types you will use most. A **resource** block describes
something Terraform creates and owns, such as the instance. A **data** block looks up something
that already exists without creating it — here, the id of the current Amazon Linux 2023 image.
Those ids change whenever AWS publishes an update, so looking one up beats typing one in.

The instance is deliberately bare. It goes into your account's default VPC and inherits that
VPC's **default security group**, which allows no inbound traffic from the internet. You will
confirm the server exists through the AWS API, not by logging into it: there is no key pair and
no SSH access in this lab. [Lab 21](lab21-capstone-vpc-ec2.md) builds the network, the security
group, and a reachable server in code.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `data.aws_ami.amazon_linux` | Finds the newest Amazon Linux 2023 image | None |
| `aws_instance.web` | One `t3.micro` virtual server in `us-east-1` | Billed per second while running |
| Outputs | Report the instance id, its public address, and the image used | None |

**This lab costs money.** A `t3.micro` costs a fraction of a cent per minute, but it bills until
destroyed — do not stop after the apply step.

## Before you start

- [ ] [Lab 02](lab02-console-vpc.md) completed
- [ ] Credentials exported in this terminal, as in [Lab 00](lab00-aws-setup-and-init.md)
- [ ] Permission to run EC2 instances in your training account
- [ ] A **default VPC** exists in `us-east-1` — check it now, before you go any further:

```bash
aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[].VpcId' --output text
```

**Expected output**

```text
vpc-0fa2e04ddfd87b3a9
```

Your id will differ. If the command prints nothing, the account has no default VPC. Create one —
it is a single command, it costs nothing, and it fixes the account for the whole track:

```bash
aws ec2 create-default-vpc
```

This matters because `main.tf` declares an `aws_instance` with no `subnet_id`. When you leave the
network out, AWS does not pick a network for you at random: it puts the instance in the region's
**default VPC** — the pre-built network AWS normally creates in every region — using that VPC's
default subnet and default security group. If no default VPC exists, there is nothing for the
instance to land in and the launch is rejected. Training accounts are the common case here,
because a default VPC can be deleted and some accounts are handed out without one.

The trap is that `terraform plan` in Step 4 will succeed either way. Planning never calls
`RunInstances`, so nothing checks for the network until Step 5 tries to create the instance for
real. Confirm the VPC now rather than reading the failure later.

## Steps

### Step 1 — Confirm your credentials are still loaded

Environment variables disappear when a terminal closes, so re-check in the window you are using.
If this fails, re-export your keys as described in Lab 00 before continuing.

```bash
aws sts get-caller-identity
```

**Expected output**

```text
{
    "UserId": "AIDA2EXAMPLEID4NEXAMPLE",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/odl_user_1234567"
}
```

### Step 2 — Move into the lab and initialize it

```bash
cd terraform/labs/lab03-first-ec2
terraform init
```

**Expected output**

```text
Terraform has been successfully initialized!
```

### Step 3 — Read the configuration

```bash
cat main.tf variables.tf outputs.tf
```

The `data "aws_ami" "amazon_linux"` block searches images owned by `amazon` whose name matches
`al2023-ami-2023.*-x86_64`, and `most_recent = true` keeps only the newest. The `aws_instance`
block refers to it as `data.aws_ami.amazon_linux.id`, and that reference is how Terraform knows
the lookup must happen first — you never state the order yourself. The region, size, and name
tag come from `variables.tf`, covered in [Lab 06](lab06-variables-outputs.md).

### Step 4 — Preview the change

`terraform plan` compares your file with what exists and reports what it would do. It changes
nothing, so it is always safe to run.

```bash
terraform plan
```

**Expected output**

```text
data.aws_ami.amazon_linux: Reading...
data.aws_ami.amazon_linux: Read complete after 1s [id=ami-0abcdef1234567890]

Terraform will perform the following actions:

  # aws_instance.web will be created
  + resource "aws_instance" "web" {
      + ami           = "ami-0abcdef1234567890"
      + instance_type = "t3.micro"
      + id            = (known after apply)
      + public_ip     = (known after apply)
      + tags          = {
          + "Lab"       = "lab03"
          + "ManagedBy" = "Terraform"
          + "Name"      = "tf-lab03-web"
        }
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```

A `+` marks something being created and `(known after apply)` marks values AWS has not assigned
yet. Read the summary line before every apply — the last point at which mistakes are free.

### Step 5 — Create the instance

```bash
terraform apply
```

Terraform shows the same plan and waits. Type `yes` and press Enter.

**Expected output**

```text
aws_instance.web: Creating...
aws_instance.web: Still creating... [10s elapsed]
aws_instance.web: Creation complete after 32s [id=i-0123456789abcdef0]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

ami_id = "ami-0abcdef1234567890"
instance_id = "i-0123456789abcdef0"
public_ip = "54.210.11.22"
```

Your ids and address will differ. Billing starts now.

### Step 6 — Read the outputs back

Outputs are stored in state, so you can query one at a time instead of re-reading the apply log.
`-raw` prints the bare value with no quotes, which is what you want when feeding it to another
command.

```bash
terraform output instance_id
terraform output -raw public_ip
```

**Expected output**

```text
"i-0123456789abcdef0"
54.210.11.22
```

If `public_ip` is empty, the subnet did not assign a public address. That is harmless here —
nothing in this lab connects to the server.

### Step 7 — Confirm the server exists

Ask AWS directly rather than trusting Terraform's word for it.

```bash
aws ec2 describe-instances --instance-ids "$(terraform output -raw instance_id)" \
  --query 'Reservations[0].Instances[0].State.Name' --output text
```

**Expected output**

```text
running
```

### Step 8 — Destroy it

This step is mandatory. Leaving the instance running keeps charging your account.

```bash
terraform destroy
```

Terraform lists what it will remove and waits. Type `yes`.

**Expected output**

```text
aws_instance.web: Destroying... [id=i-0123456789abcdef0]
aws_instance.web: Still destroying... [id=i-0123456789abcdef0, 30s elapsed]
aws_instance.web: Destruction complete after 41s

Destroy complete! Resources: 1 destroyed.
```

## Done when

- [ ] `terraform plan` showed `1 to add`
- [ ] `terraform apply` printed an `instance_id` starting with `i-`
- [ ] The AWS CLI reported the instance as `running`
- [ ] `terraform destroy` reported `1 destroyed`
- [ ] No instance tagged `Lab = lab03` remains in the EC2 console

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `No valid credential sources found` | Keys not exported in this terminal | Re-export them, then retry |
| `VPCIdNotSpecified: No default VPC for this user` on apply, after a clean plan | The account has no default VPC for the instance to launch into | `aws ec2 create-default-vpc`, then `terraform apply` again |
| `UnauthorizedOperation` | Training account may not allow `RunInstances` | A policy limit, not a broken key; ask for the permission |
| `InvalidAMIID.NotFound` | Region is not `us-east-1` | Check `AWS_DEFAULT_REGION` and `var.aws_region` |
| `VcpuLimitExceeded` | Account instance limit reached | Destroy other instances or request a limit increase |
| `public_ip` output is empty | The default subnet assigns no public address | Harmless here; Lab 21 configures this explicitly |
| Plan shows `0 to add` | Already applied, or wrong directory | Check `pwd`, then `terraform state list` |
| Destroy fails partway | A transient AWS error | Run `terraform destroy` again; it is safe to repeat |

## Cleanup

```bash
terraform destroy
```

If destroy fails and you terminate the instance in the console instead, tell Terraform it is
gone so its records match reality:

```bash
terraform state rm aws_instance.web
```

## Next steps

- Deep dive: [Resources](../docs/basic/03-resources.md)
- Visual: [Basic tier concepts](../html/basic.html)
- Continue to [Lab 04 — Plan, apply, destroy](lab04-plan-apply-destroy.md)
