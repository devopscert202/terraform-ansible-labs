# Lab 02 — Building a Network by Hand in the Console

| | |
|---|---|
| **Goal** | Build a small public network by clicking through the AWS console, verify each piece from the command line, then delete it by hand — so you feel the problem Terraform solves. |
| **Time** | 60–75 minutes |
| **Tier** | Basic |
| **Files** | `../labs/lab02-console-vpc/` (README only — this lab has no Terraform code) |

## Overview

This is the one lab in the track with no `.tf` files. You will build a network the manual way,
in the AWS web console, and count the clicks. Later, [Lab 21](lab21-capstone-vpc-ec2.md) builds
the same shape from a single file with one command.

Five pieces make a network in AWS. A **VPC** is your own private slice of the AWS network. A
**subnet** is a smaller range of addresses inside it, tied to one data centre. An **internet
gateway** is the door between that network and the public internet. A **route table** is the
signpost that says "traffic for anywhere else goes out that door". A **security group** is a
firewall listing which traffic is allowed to reach a machine. You need all five, in that order,
before a server can be reached from the internet.

After each console screen you will confirm the result with the AWS CLI. The console and the CLI
read the same account, so this is how you check your own work — and it is the same information
Terraform reads when it builds a plan.

## What you will build

| Resource | Terraform type (used in Lab 21) | Cost |
|---|---|---|
| VPC `10.0.0.0/16` | `aws_vpc` | None |
| Public subnet `10.0.1.0/24` | `aws_subnet` | None |
| Internet gateway | `aws_internet_gateway` | None |
| Route `0.0.0.0/0` to the gateway | `aws_route_table`, `aws_route` | None |
| Security group, inbound SSH | `aws_security_group` | None |

Every object here is free. Nothing is billed unless you launch a server, which this lab does not.

## Before you start

- [ ] [Lab 01](lab01-providers-init.md) completed
- [ ] Sign-in access to the AWS console for your training account
- [ ] AWS CLI credentials working, as set up in [Lab 00](lab00-aws-setup-and-init.md)
- [ ] Region set to **us-east-1** in the console's top-right region selector

## Steps

### Step 1 — Confirm you are in the training account

Everything you create here is real and lives in a real account. Check which one before clicking.

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

Stop if the account number is not your training account.

### Step 2 — Create the VPC

In the console, go to **VPC → Your VPCs → Create VPC**.

| Setting | Value |
|---|---|
| Resources to create | VPC only |
| Name tag | `console-lab-vpc` |
| IPv4 CIDR block | `10.0.0.0/16` |
| Tenancy | Default |

A **CIDR block** is a range of IP addresses written as an address plus a slash number. The
smaller the number after the slash, the larger the range: `/16` gives about 65,000 addresses.

### Step 3 — Verify the VPC from the command line

```bash
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=console-lab-vpc" \
  --query 'Vpcs[0].{VpcId:VpcId,Cidr:CidrBlock,State:State}'
```

**Expected output**

```text
{
    "VpcId": "vpc-0a1b2c3d4e5f67890",
    "Cidr": "10.0.0.0/16",
    "State": "available"
}
```

Write down the `VpcId`. AWS generated it — you cannot choose it, and you will need it repeatedly.

### Step 4 — Create a public subnet

Go to **VPC → Subnets → Create subnet**.

| Setting | Value |
|---|---|
| VPC ID | `console-lab-vpc` |
| Subnet name | `console-lab-public-a` |
| Availability Zone | `us-east-1a` |
| IPv4 CIDR block | `10.0.1.0/24` |

An **availability zone** is one physical data centre within the region. A subnet lives in exactly
one zone, which is why real systems spread across several.

### Step 5 — Verify the subnet

```bash
aws ec2 describe-subnets --filters "Name=tag:Name,Values=console-lab-public-a" \
  --query 'Subnets[0].{SubnetId:SubnetId,VpcId:VpcId,Cidr:CidrBlock,Az:AvailabilityZone}'
```

**Expected output**

```text
{
    "SubnetId": "subnet-0f1e2d3c4b5a69870",
    "VpcId": "vpc-0a1b2c3d4e5f67890",
    "Cidr": "10.0.1.0/24",
    "Az": "us-east-1a"
}
```

Check that `VpcId` matches the value from Step 3. Nothing in the console stopped you from
putting this subnet in the wrong VPC; you have to notice that yourself.

### Step 6 — Create and attach an internet gateway

Go to **VPC → Internet gateways → Create internet gateway**, name it `console-lab-igw`, then
choose **Actions → Attach to VPC** and pick `console-lab-vpc`.

Creating and attaching are two separate actions. A gateway that exists but is not attached does
nothing — a distinction that is easy to miss by hand and impossible to miss in code.

### Step 7 — Verify the gateway attachment

```bash
aws ec2 describe-internet-gateways --filters "Name=tag:Name,Values=console-lab-igw" \
  --query 'InternetGateways[0].{IgwId:InternetGatewayId,Attachments:Attachments}'
```

**Expected output**

```text
{
    "IgwId": "igw-07a8b9c0d1e2f3456",
    "Attachments": [
        {
            "State": "available",
            "VpcId": "vpc-0a1b2c3d4e5f67890"
        }
    ]
}
```

An empty `Attachments` list means the gateway was created but never attached.

### Step 8 — Add a route to the internet

Go to **VPC → Route tables**, select the main route table for `console-lab-vpc`, then
**Routes → Edit routes → Add route**.

| Destination | Target |
|---|---|
| `0.0.0.0/0` | `console-lab-igw` |

`0.0.0.0/0` means "every address not already matched". Without this line the subnet is private:
the gateway is attached, but nothing knows to use it.

### Step 9 — Verify the route and the subnet association

A route table only affects subnets associated with it. Check both facts at once.

```bash
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=vpc-0a1b2c3d4e5f67890" \
  --query 'RouteTables[0].{Routes:Routes,Associations:Associations[].SubnetId}'
```

**Expected output**

```text
{
    "Routes": [
        {
            "DestinationCidrBlock": "10.0.0.0/16",
            "GatewayId": "local",
            "State": "active"
        },
        {
            "DestinationCidrBlock": "0.0.0.0/0",
            "GatewayId": "igw-07a8b9c0d1e2f3456",
            "State": "active"
        }
    ],
    "Associations": [
        null
    ]
}
```

The `local` route was created with the VPC and carries traffic inside it. A `null` association
means the subnet uses this table only because it is the VPC's main table, not because anyone
attached it — a default that is easy to rely on by accident.

### Step 10 — Find your own public address

A security group rule needs a source address. Use your own, not the whole internet.

```bash
curl -s ifconfig.me
```

**Expected output**

```text
203.0.113.10
```

### Step 11 — Create the security group

Go to **VPC → Security groups → Create security group**.

| Setting | Value |
|---|---|
| Name | `console-lab-sg` |
| VPC | `console-lab-vpc` |
| Inbound rule | SSH, TCP 22, source `203.0.113.10/32` (your address) |
| Outbound rule | All traffic (the default) |

`/32` means exactly one address: yours. Never open SSH to `0.0.0.0/0` — that offers the whole
internet a login prompt.

### Step 12 — Verify the security group rule

```bash
aws ec2 describe-security-groups --filters "Name=group-name,Values=console-lab-sg" \
  --query 'SecurityGroups[0].{GroupId:GroupId,Ingress:IpPermissions}'
```

**Expected output**

```text
{
    "GroupId": "sg-0192a3b4c5d6e7f80",
    "Ingress": [
        {
            "FromPort": 22,
            "IpProtocol": "tcp",
            "IpRanges": [
                {
                    "CidrIp": "203.0.113.10/32"
                }
            ],
            "ToPort": 22
        }
    ]
}
```

Confirm `CidrIp` is your address with `/32`, not `0.0.0.0/0`.

### Step 13 — Record what you built

Every object AWS created got an id you did not choose. Write them down — you need them to delete
things in the right order, and they are the same strings Terraform will keep in its state file.

| Object | Your id | Terraform address in Lab 21 |
|---|---|---|
| VPC | `vpc-…` | `aws_vpc.main.id` |
| Subnet | `subnet-…` | `aws_subnet.public.id` |
| Internet gateway | `igw-…` | `aws_internet_gateway.main.id` |
| Security group | `sg-…` | `aws_security_group.web.id` |

In Lab 21 you never see these ids. One resource refers to another by name, and Terraform fills
in the generated id at apply time.

### Step 14 — Count the work

You have created five objects across five console screens and run six commands to check them,
and each object had to be pointed at the one before it. Nothing recorded the order, nothing can
repeat it, and nobody else can review it before it happens. Lab 21 builds this same network from
a file of about forty lines, applies in one command, and destroys in one more.

## Done when

- [ ] `console-lab-vpc` shows state `available`
- [ ] `console-lab-public-a` exists in `us-east-1a` inside that VPC
- [ ] `console-lab-igw` shows an attachment in state `available`
- [ ] The route table has a `0.0.0.0/0` route to the gateway
- [ ] `console-lab-sg` allows SSH from your address only
- [ ] Every object above has been deleted again

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `DependencyViolation` when deleting | Something inside still uses it | Delete in the order given under Cleanup |
| Cannot attach the gateway | A VPC may hold only one | Detach the existing gateway or use your new VPC |
| CIDR overlap error | `10.0.0.0/16` already exists here | Delete the old VPC or use `10.10.0.0/16` |
| Objects missing from the console | Wrong region selected | Switch the region selector to `us-east-1` |
| A CLI query returns `null` | The name tag does not match | Check the Name tag spelling in the console |
| `UnauthorizedOperation` | Training account policy limit | Not a broken credential; ask for the permission |

## Cleanup

Delete by hand, in this order — each object must go before the one it depends on.

1. Detach, then delete, the internet gateway `console-lab-igw`
2. Delete the security group `console-lab-sg`
3. Delete the subnet `console-lab-public-a`
4. Delete the VPC `console-lab-vpc`

Confirm nothing is left:

```bash
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=console-lab-vpc" --query 'Vpcs'
aws ec2 describe-security-groups --filters "Name=group-name,Values=console-lab-sg" \
  --query 'SecurityGroups'
```

**Expected output**

```text
[]
[]
```

Two empty lists confirm both are gone. Leaving them costs nothing, but a stray network is
exactly the kind of untracked leftover Terraform exists to prevent.

## Next steps

- Deep dive: [Resources](../docs/basic/03-resources.md)
- Visual: [Basic tier concepts](../html/basic.html)
- Continue to [Lab 03 — Your first EC2 instance](lab03-first-ec2.md)
