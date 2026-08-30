# Lab 03 — Your First EC2 Instance

| | |
|---|---|
| **Goal** | Build a VPC, two subnets, and a security group, launch one EC2 instance inside them, confirm it through the AWS API, then destroy everything. |
| **Time** | 35–45 minutes |
| **Tier** | Basic |
| **Files** | `../labs/lab03-first-ec2/` |

## Overview

In [Lab 02](lab02-console-vpc.md) you clicked through the console. Now you describe infrastructure
in a file and let Terraform build it. An **EC2 instance** is a virtual machine running in AWS,
charged by the second while it exists. Every instance must live in a **subnet**, and every subnet
lives in a **VPC** — your own private network inside AWS, defined by a **CIDR block** such as
`10.0.0.0/16` (a range of IP addresses written as an address plus a prefix length).

This lab builds that network itself rather than borrowing one. That is a deliberate choice: an
`aws_instance` with no `subnet_id` falls back to the region's *default VPC*, an account can be
handed to you without one, and the failure surfaces only at apply. Declaring the network removes
the guesswork — the instance lands where you said it lands.

Two block types do the work. A **resource** block describes something Terraform creates and owns.
A **data** block looks up something that already exists without creating it — here, the id of the
current Amazon Linux 2023 image, which changes whenever AWS publishes an update.

Nothing in this lab is reachable from the internet, and that is intentional. There is no key pair,
no public IP, and no SSH from your laptop.
[Lab 10](lab10-capstone-vpc-ec2.md) adds the internet gateway and the route that make a subnet
genuinely public.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `data.aws_ami.amazon_linux` | Finds the newest Amazon Linux 2023 image | None |
| `aws_vpc.main` | The `10.0.0.0/16` network everything else sits in | Free |
| `aws_subnet.public` | `10.0.1.0/24` in `us-east-2a`; the instance launches here | Free |
| `aws_subnet.private` | `10.0.2.0/24` in `us-east-2b` | Free |
| `aws_security_group.instance` | Firewall: inbound TCP 22 from the VPC range only, all outbound | Free |
| `aws_instance.web` | One `t3.micro` virtual server | Billed per second while running |

Five managed resources and one data source. VPCs, subnets, and security groups cost nothing. The
`t3.micro` is the only billable item and it bills until destroyed, so do not stop after the apply
step.

### "public" is a name, not a fact

`aws_subnet.public` is **not a public subnet yet.** A subnet is public only when its route table
sends `0.0.0.0/0` to an internet gateway. This lab creates no gateway and no route table, so both
subnets are private: nothing in either one can reach the internet, and nothing on the internet can
reach into them. The name records the role the subnet will play in the capstone, where the gateway
and the route are added and the word finally becomes true.

Two consequences follow, and you will verify both with the AWS CLI:

- The instance gets a **private IP only**. There is no public address to connect to.
- Port 22 is open to `var.vpc_cidr` and to nothing else. Another instance inside the VPC could
  SSH in; your laptop cannot, even with a key. Never widen that to `0.0.0.0/0` to "make it work".

## Before you start

- [ ] [Lab 02](lab02-console-vpc.md) completed
- [ ] Credentials exported in this terminal, as in [Lab 00](lab00-aws-setup-and-init.md)
- [ ] Permission to run EC2 instances and create VPCs in your training account
- [ ] Lab code at [`../labs/lab03-first-ec2/`](../labs/lab03-first-ec2/)

Confirm the credentials are loaded in the window you are actually using — environment variables
disappear when a terminal closes.

```bash
aws sts get-caller-identity
```

**Expected output**

```text
{
    "UserId": "AIDA5HIGYY7IX72SW4PEP",
    "Account": "908936660945",
    "Arn": "arn:aws:iam::908936660945:user/odl_user_2369039"
}
```

## Steps

### Step 1 — Enter the lab directory and initialize it

`terraform init` downloads the AWS provider into `.terraform/`. Every other command needs it, so
it comes first.

```bash
cd terraform/labs/lab03-first-ec2
ls *.tf terraform.tfvars.example
terraform init
```

**Expected output**

```text
main.tf
outputs.tf
terraform.tfvars.example
variables.tf
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.100.0...
- Installed hashicorp/aws v5.100.0 (signed by HashiCorp)
Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository
so that Terraform can guarantee to make the same selections by default when
you run "terraform init" in the future.

Terraform has been successfully initialized!
```

### Step 2 — Read the inputs

Nothing in `main.tf` hardcodes a CIDR, a zone, or a name. Every one of those is a **variable**: a
named input with a declared type, a description, and here a default value.

```bash
grep '^variable' variables.tf
```

**Expected output**

```text
variable "aws_region" {
variable "vpc_cidr" {
variable "public_subnet_cidr" {
variable "private_subnet_cidr" {
variable "public_subnet_az" {
variable "private_subnet_az" {
variable "instance_type" {
variable "instance_name" {
```

Open `variables.tf` and read the full declarations. All eight are `type = string`, and all eight
carry a `default`, which is why the lab applies with no input from you at all.

| Variable | Default | What it controls |
|---|---|---|
| `aws_region` | `us-east-2` | The region the provider talks to |
| `vpc_cidr` | `10.0.0.0/16` | The VPC's address range, **and** the only range allowed to reach port 22 |
| `public_subnet_cidr` | `10.0.1.0/24` | The subnet the instance launches into; must sit inside `vpc_cidr` |
| `private_subnet_cidr` | `10.0.2.0/24` | The second subnet; must sit inside `vpc_cidr` and not overlap the first |
| `public_subnet_az` | `us-east-2a` | Availability zone of the first subnet |
| `private_subnet_az` | `us-east-2b` | Availability zone of the second subnet |
| `instance_type` | `t3.micro` | Instance size |
| `instance_name` | `tf-lab03-web` | The instance's `Name` tag and the prefix for every other resource name |

An **availability zone** is one isolated group of datacentres inside a region. A subnet lives in
exactly one. `us-east-2` has three: `us-east-2a`, `us-east-2b`, and `us-east-2c`. The two zones
here are plain variables so you can see and change them; a zone name that does not exist in the
region is rejected at apply, and the `If something fails` table below carries that exact error.

### Step 3 — Copy the example tfvars and change two values

A `terraform.tfvars` file supplies values without editing `variables.tf`. The repository ships an
example; real `terraform.tfvars` files are gitignored because they routinely hold environment
detail you do not want committed.

```bash
cp terraform.tfvars.example terraform.tfvars
```

Now edit `terraform.tfvars`. Change the name and move the whole network to a different range —
`vpc_cidr` and both subnet CIDRs together, since a subnet must fall inside its VPC:

```hcl
vpc_cidr            = "10.10.0.0/16"
public_subnet_cidr  = "10.10.1.0/24"
private_subnet_cidr = "10.10.2.0/24"
instance_name       = "tf-lab03-demo"
```

### Step 4 — Prove the override reached the plan

`terraform plan` compares your configuration against what exists and reports what it would do. It
creates nothing, so it is always safe to run. Filter it down to the values you just changed:

```bash
terraform plan -no-color | grep -E '\+ *(cidr_block|"Name") +=' | sort -u
```

**Expected output**

```text
          + "Name"      = "tf-lab03-demo-private"
          + "Name"      = "tf-lab03-demo-public"
          + "Name"      = "tf-lab03-demo-sg"
          + "Name"      = "tf-lab03-demo-vpc"
          + "Name"      = "tf-lab03-demo"
      + cidr_block                                     = "10.10.1.0/24"
      + cidr_block                                     = "10.10.2.0/24"
      + cidr_block                           = "10.10.0.0/16"
```

Before the tfvars file existed, the same command against the defaults printed this:

```text
          + "Name"      = "tf-lab03-web-private"
          + "Name"      = "tf-lab03-web-public"
          + "Name"      = "tf-lab03-web-sg"
          + "Name"      = "tf-lab03-web-vpc"
          + "Name"      = "tf-lab03-web"
      + cidr_block                                     = "10.0.1.0/24"
      + cidr_block                                     = "10.0.2.0/24"
      + cidr_block                           = "10.0.0.0/16"
```

One edit changed five resource names, because `instance_name` is the prefix for all of them, and
three CIDRs. **`terraform.tfvars` beats the `default` in `variables.tf`.** The default is the
fallback used when nobody supplies a value, not a fixed setting.

### Step 5 — Override the override with `-var`

`-var` on the command line outranks `terraform.tfvars`. Leave the file exactly as it is and run:

```bash
terraform plan -no-color -var 'instance_name=tf-lab03-cli' | grep -E '\+ *(cidr_block|"Name") +=' | sort -u
```

**Expected output**

```text
          + "Name"      = "tf-lab03-cli-private"
          + "Name"      = "tf-lab03-cli-public"
          + "Name"      = "tf-lab03-cli-sg"
          + "Name"      = "tf-lab03-cli-vpc"
          + "Name"      = "tf-lab03-cli"
      + cidr_block                                     = "10.10.1.0/24"
      + cidr_block                                     = "10.10.2.0/24"
      + cidr_block                           = "10.10.0.0/16"
```

The names came from `-var`; the CIDRs still came from `terraform.tfvars`, which is still supplying
every variable `-var` did not mention. Precedence, lowest to highest:

`default` in `variables.tf` → `terraform.tfvars` → `-var` on the command line

[Lab 07](lab07-tfvars-secrets.md) covers the remaining sources and the rules for secrets.

### Step 6 — Read `main.tf` and trace the dependency chain

```bash
cat main.tf
```

You never tell Terraform what order to build in. It reads the references between resources and
derives the order itself:

| Resource | References | So it must wait for |
|---|---|---|
| `aws_vpc.main` | `var.vpc_cidr` only | nothing — built first |
| `aws_subnet.public` | `aws_vpc.main.id` | the VPC |
| `aws_subnet.private` | `aws_vpc.main.id` | the VPC |
| `aws_security_group.instance` | `aws_vpc.main.id` | the VPC |
| `aws_instance.web` | `aws_subnet.public.id`, `aws_security_group.instance.id`, `data.aws_ami.amazon_linux.id` | both of those, and the AMI lookup |

`aws_vpc.main.id` is not known until AWS has created the VPC, so writing that reference *is* the
instruction "do the VPC first". The three middle resources reference only the VPC and never each
other, so Terraform creates them in parallel. The instance is last because it depends on two of
them.

Two lines deserve a second look. In the security group:

```hcl
cidr_blocks = [var.vpc_cidr]
```

Port 22 is scoped to the VPC's own range. Because it is the *variable* and not a literal, moving
the network in Step 3 moved the allowed source range with it — that is why the plan showed
`10.10.0.0/16` inside the ingress rule. And on the instance:

```hcl
subnet_id              = aws_subnet.public.id
vpc_security_group_ids = [aws_security_group.instance.id]
```

Stating both is what makes the default VPC irrelevant. There is no `associate_public_ip_address`
and no `map_public_ip_on_launch`, so no public address is assigned.

### Step 7 — Check formatting and validate

```bash
terraform fmt -check
terraform validate
```

**Expected output**

```text
Success! The configuration is valid.
```

`terraform fmt -check` prints nothing and exits 0 when every file is already canonically
formatted. If it lists a filename, run `terraform fmt` to rewrite it. `validate` checks syntax and
types locally; it makes no AWS calls, so it cannot tell you whether a CIDR or a zone is acceptable
to AWS.

### Step 8 — Read the full plan

```bash
terraform plan
```

**Expected output** (trimmed — the `aws_instance` block alone runs to 70 lines)

```text
data.aws_ami.amazon_linux: Reading...
data.aws_ami.amazon_linux: Read complete after 2s [id=ami-01042494dba64ab96]

Terraform used the selected providers to generate the following execution
plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # aws_instance.web will be created
  + resource "aws_instance" "web" {
      + ami                                  = "ami-01042494dba64ab96"

... 4 more resource blocks ...

Plan: 5 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + instance_id         = (known after apply)
  + instance_private_ip = (known after apply)
  + private_subnet_az   = "us-east-2b"
  + private_subnet_id   = (known after apply)
  + public_subnet_az    = "us-east-2a"
  + public_subnet_id    = (known after apply)
  + security_group_id   = (known after apply)
  + vpc_id              = (known after apply)
```

`+` marks something being created; `(known after apply)` marks a value AWS has not assigned yet.
`Plan: 5 to add` is the count to check: VPC, two subnets, security group, instance. The data source
is not in it — it read, it did not create. Your AMI id will differ, and it should: `most_recent`
resolves whatever Amazon published last.

The two zone outputs already show concrete values because they come straight from variables, while
every id waits for AWS.

### Step 9 — Apply

```bash
terraform apply
```

Terraform prints the same plan and waits. Type `yes` and press Enter; nothing else is accepted.

**Expected output**

```text
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

aws_vpc.main: Creating...
aws_vpc.main: Still creating... [00m10s elapsed]
aws_vpc.main: Creation complete after 15s [id=vpc-0edee6d974d6ffc45]
aws_subnet.private: Creating...
aws_subnet.public: Creating...
aws_security_group.instance: Creating...
aws_subnet.public: Creation complete after 2s [id=subnet-055d0bd49aeeb4443]
aws_subnet.private: Creation complete after 2s [id=subnet-0c07c65cb08a413be]
aws_security_group.instance: Creation complete after 6s [id=sg-09d005205da2821e8]
aws_instance.web: Creating...
aws_instance.web: Still creating... [00m10s elapsed]
aws_instance.web: Creation complete after 15s [id=i-015b4097e89730013]

Apply complete! Resources: 5 added, 0 changed, 0 destroyed.

Outputs:

instance_id = "i-015b4097e89730013"
instance_private_ip = "10.10.1.115"
private_subnet_az = "us-east-2b"
private_subnet_id = "subnet-0c07c65cb08a413be"
public_subnet_az = "us-east-2a"
public_subnet_id = "subnet-055d0bd49aeeb4443"
security_group_id = "sg-09d005205da2821e8"
vpc_id = "vpc-0edee6d974d6ffc45"
```

Read the ordering: the VPC finishes alone, then all three VPC-dependent resources start in the same
second, then the instance. That is the table from Step 6 executing. Billing starts now.

### Step 10 — Read the outputs back

Outputs are stored in state, so query them any time instead of scrolling the apply log. `-raw`
prints one bare value with no quotes, which is what you feed to another command.

```bash
terraform output
terraform output -raw instance_private_ip
```

**Expected output**

```text
instance_id = "i-015b4097e89730013"
instance_private_ip = "10.10.1.115"
private_subnet_az = "us-east-2b"
private_subnet_id = "subnet-0c07c65cb08a413be"
public_subnet_az = "us-east-2a"
public_subnet_id = "subnet-055d0bd49aeeb4443"
security_group_id = "sg-09d005205da2821e8"
vpc_id = "vpc-0edee6d974d6ffc45"
10.10.1.115
```

There is no `public_ip` output, because there is no public IP to report.

### Step 11 — Confirm the network with the AWS CLI

Ask AWS directly rather than trusting Terraform's word for it.

```bash
aws ec2 describe-vpcs --vpc-ids "$(terraform output -raw vpc_id)" \
  --query 'Vpcs[0].{VpcId:VpcId,CidrBlock:CidrBlock,IsDefault:IsDefault,State:State}' --output json
```

**Expected output**

```text
{
    "VpcId": "vpc-0edee6d974d6ffc45",
    "CidrBlock": "10.10.0.0/16",
    "IsDefault": false,
    "State": "available"
}
```

`"IsDefault": false` is the point of this lab: the instance is in a network you declared, not in
whatever the account happened to have lying around.

```bash
aws ec2 describe-subnets --filters "Name=vpc-id,Values=$(terraform output -raw vpc_id)" \
  --query 'sort_by(Subnets,&CidrBlock)[].{Name:Tags[?Key==`Name`]|[0].Value,Cidr:CidrBlock,AZ:AvailabilityZone,MapPublicIp:MapPublicIpOnLaunch}' \
  --output table
```

**Expected output**

```text
------------------------------------------------------------------------
|                            DescribeSubnets                           |
+------------+---------------+--------------+--------------------------+
|     AZ     |     Cidr      | MapPublicIp  |          Name            |
+------------+---------------+--------------+--------------------------+
|  us-east-2a|  10.10.1.0/24 |  False       |  tf-lab03-demo-public    |
|  us-east-2b|  10.10.2.0/24 |  False       |  tf-lab03-demo-private   |
+------------+---------------+--------------+--------------------------+
```

`MapPublicIp` is `False` on **both** rows. The one called `public` is no more public than the other
one — that is the honest state of this lab, and Lab 10 is where the difference appears.

### Step 12 — Confirm port 22 is scoped to the VPC

```bash
aws ec2 describe-security-groups --group-ids "$(terraform output -raw security_group_id)" \
  --query 'SecurityGroups[0].IpPermissions' --output json
```

**Expected output**

```text
[
    {
        "IpProtocol": "tcp",
        "FromPort": 22,
        "ToPort": 22,
        "UserIdGroupPairs": [],
        "IpRanges": [
            {
                "Description": "SSH from within the VPC",
                "CidrIp": "10.10.0.0/16"
            }
        ],
        "Ipv6Ranges": [],
        "PrefixListIds": []
    }
]
```

One rule, one source range, and that range is the VPC's own — `10.10.0.0/16` here because Step 3
moved the network. `0.0.0.0/0` appears nowhere in the ingress. If you ever see it there on port 22,
the instance is offered to every scanner on the internet.

### Step 13 — Confirm the instance has no public address

```bash
aws ec2 describe-instances --instance-ids "$(terraform output -raw instance_id)" \
  --query 'Reservations[0].Instances[0].{State:State.Name,PrivateIp:PrivateIpAddress,PublicIp:PublicIpAddress,SubnetId:SubnetId,AZ:Placement.AvailabilityZone}' \
  --output json
```

**Expected output**

```text
{
    "State": "running",
    "PrivateIp": "10.10.1.115",
    "PublicIp": null,
    "SubnetId": "subnet-055d0bd49aeeb4443",
    "AZ": "us-east-2a"
}
```

`running`, holding a private address inside `10.10.1.0/24`, in the subnet Terraform reported, in
the zone the variable named. `"PublicIp": null` — AWS assigned none, so there is no address to
`ssh` to or `curl` from your laptop. The server is real and working; it is simply not exposed.

```bash
terraform state list
```

**Expected output**

```text
data.aws_ami.amazon_linux
aws_instance.web
aws_security_group.instance
aws_subnet.private
aws_subnet.public
aws_vpc.main
```

### Step 14 — Destroy

Mandatory. The instance bills until it is gone.

```bash
terraform destroy
```

Terraform lists what it will remove and waits for the same `yes`.

**Expected output**

```text
Plan: 0 to add, 0 to change, 5 to destroy.

Do you really want to destroy all resources?
  Terraform will destroy all your managed infrastructure, as shown above.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value: yes

aws_subnet.private: Destroying... [id=subnet-0c07c65cb08a413be]
aws_instance.web: Destroying... [id=i-015b4097e89730013]
aws_subnet.private: Destruction complete after 2s
aws_instance.web: Still destroying... [id=i-015b4097e89730013, 00m10s elapsed]
aws_instance.web: Still destroying... [id=i-015b4097e89730013, 00m20s elapsed]
aws_instance.web: Destruction complete after 22s
aws_subnet.public: Destroying... [id=subnet-055d0bd49aeeb4443]
aws_security_group.instance: Destroying... [id=sg-09d005205da2821e8]
aws_subnet.public: Destruction complete after 1s
aws_security_group.instance: Destruction complete after 1s
aws_vpc.main: Destroying... [id=vpc-0edee6d974d6ffc45]
aws_vpc.main: Destruction complete after 1s

Destroy complete! Resources: 5 destroyed.
```

Destruction runs the Step 6 chain backwards. `aws_subnet.private` goes immediately because nothing
uses it, while `aws_subnet.public` has to wait 22 seconds for the instance inside it to terminate.
The VPC goes last, once nothing is left in it.

## Done when

- [ ] The tfvars plan showed your edited name and CIDRs; the `-var` plan overrode the name but kept the tfvars CIDRs
- [ ] `terraform plan` reported `5 to add, 0 to change, 0 to destroy`
- [ ] `terraform apply` reported `5 added` and printed eight outputs, none of them a public IP
- [ ] `describe-vpcs` reported `"IsDefault": false`
- [ ] `describe-security-groups` showed exactly one ingress rule: TCP 22 from the VPC CIDR, not `0.0.0.0/0`
- [ ] `describe-instances` reported `running` with a private IP and `"PublicIp": null`
- [ ] `terraform destroy` reported `5 destroyed` and `terraform state list` then printed nothing

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `No valid credential sources found` | Keys not exported in this terminal | Re-export them as in Lab 00, then retry |
| `InvalidSubnet.Range: The CIDR '192.168.5.0/24' is invalid` on apply | A subnet CIDR is not inside `vpc_cidr` | Put both subnet CIDRs inside the VPC range — with `10.0.0.0/16`, use `10.0.x.0/24` |
| `InvalidParameterValue: Value (us-east-2f) for parameter availabilityZone is invalid` | A zone variable names a zone the region does not have | The message lists the valid zones; `us-east-2` has `us-east-2a`, `us-east-2b`, `us-east-2c` |
| `InvalidSubnet.Conflict: The CIDR '...' conflicts with another subnet` | The two subnet CIDRs overlap | Give them non-overlapping ranges, e.g. `10.0.1.0/24` and `10.0.2.0/24` |
| `UnauthorizedOperation` | Training account policy may not allow `RunInstances` or `CreateVpc` | A permission boundary, not a broken key; ask for the permission |
| `InvalidAMIID.NotFound` or `Your query returned no results` | Region is not `us-east-2` | Check `AWS_DEFAULT_REGION` and `var.aws_region` |
| `VcpuLimitExceeded` | Account instance limit reached | Destroy other instances or request a limit increase |
| `InsufficientInstanceCapacity` on launch | The chosen zone has no `t3.micro` right now | Set `public_subnet_az` to another zone and re-apply |
| `DependencyViolation` on destroy | Something Terraform does not manage is still attached inside the VPC — a manually created ENI, subnet, or security group | Delete it in the console, then rerun `terraform destroy`; the VPC cannot be removed while anything lives in it |
| Plan shows `0 to add` | Already applied, or wrong directory | Check `pwd`, then `terraform state list` |
| Destroy fails partway | Usually a transient AWS error | Run `terraform destroy` again; it is safe to repeat |

## Cleanup

```bash
terraform destroy
terraform state list          # must print nothing
rm -f terraform.tfvars
rm -rf .terraform terraform.tfstate*
```

If destroy fails and you delete a resource in the console instead, tell Terraform it is gone so its
records match reality:

```bash
terraform state rm aws_instance.web
```

## Next steps

- Deep dive: [Resources](../docs/02-resources.md)
- Visual: [Basic tier concepts](../html/basic.html)
- Continue to [Lab 04 — Plan, Apply, and Destroy](lab04-plan-apply-destroy.md)
