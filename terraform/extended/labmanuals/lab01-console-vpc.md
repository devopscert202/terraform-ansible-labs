# Lab 01 — Console VPC

> **Goal:** Create and inspect a non-production VPC entirely in the AWS console, then map each component to Terraform resources used in later labs.
> **Time:** ~60 min · **Difficulty:** Beginner · **Files:** `labs/lab01-console-vpc/` (reference only — no Terraform)

## Overview

Before Terraform automates networking, operators must understand what the console creates. This lab is **console-only** — no `.tf` files and no `terraform` commands. You build a minimal public VPC pattern by hand, verify each component with the AWS CLI, document how each object maps to Terraform resource types, and delete everything before leaving the lab.

The README in `labs/lab01-console-vpc/` states explicitly that no Terraform configuration is included. That is intentional: you are building mental models for plans you will read in Essentials Lab 07 and Extended capstone projects.

## Learning objectives

- Create a VPC with DNS hostnames and DNS resolution enabled
- Create a public subnet in a single availability zone
- Attach an internet gateway and add a default public route
- Create a security group with SSH restricted to your IP (`/32`)
- Verify resources with AWS CLI (`describe-vpcs`, `describe-subnets`, etc.)
- Document console resource IDs alongside Terraform resource type names
- Delete resources in safe dependency order

## Prerequisites

- [ ] AWS console access to a **training** account (not production)
- [ ] AWS CLI installed and configured (`aws --version`)
- [ ] `export AWS_PROFILE=training` (replace with your lab profile name)
- [ ] Ability to find your public IP: `curl -s ifconfig.me`
- [ ] No Terraform required for this lab

## What you will build

```
                    Internet
                        │
                        ▼
              ┌─────────────────┐
              │ Internet Gateway │
              │ console-lab-igw  │
              └────────┬────────┘
                       │
         ┌─────────────▼─────────────┐
         │  VPC 10.99.0.0/16         │
         │  console-lab-vpc          │
         │  ┌─────────────────────┐  │
         │  │ Subnet 10.99.1.0/24 │  │
         │  │ console-lab-public-a│  │
         │  │  + route 0.0.0.0/0  │  │
         │  │  + SG (SSH /32)     │  │
         │  └─────────────────────┘  │
         └───────────────────────────┘
```

| Console object | Terraform resource (later labs) |
|----------------|--------------------------------|
| VPC | `aws_vpc` |
| Subnet | `aws_subnet` |
| Internet gateway | `aws_internet_gateway` |
| Route table + route | `aws_route_table`, `aws_route` |
| Security group | `aws_security_group` |
| EC2 (optional) | `aws_instance` |

---

## Exercise 1 — Verify AWS identity

<a id="ex1"></a>

### Step 1.1 — Set profile and verify account

```bash
export AWS_PROFILE=training
aws sts get-caller-identity
```

**Validate**

```json
{
    "UserId": "AIDAXXXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-lab-user"
}
```

Note the **Account** ID. If it does not match your training account, stop.

**What happened:** The same credential chain Terraform uses starts here. Never embed `access_key` in HCL — use profiles or IAM roles.

### Step 1.2 — Record region

```bash
export AWS_REGION=us-east-1
aws configure get region
```

**Validate** — region matches where you will create the VPC.

**What happened:** VPCs are regional. Subnet AZs must exist in this region.

---

## Exercise 2 — Create the VPC

<a id="ex2"></a>

### Step 2.1 — Create VPC in console

Navigate: **VPC** → **Your VPCs** → **Create VPC**.

| Setting | Value |
|---------|-------|
| Resources to create | VPC only (not wizard with subnets) |
| Name tag | `console-lab-vpc` |
| IPv4 CIDR block | `10.99.0.0/16` |
| IPv6 | No IPv6 CIDR |
| Tenancy | Default |
| DNS hostnames | Enable |
| DNS resolution | Enable |

**Validate** — VPC state `available` in console.

**What happened:** Equivalent to:

```hcl
resource "aws_vpc" "this" {
  cidr_block           = "10.99.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = { Name = "console-lab-vpc" }
}
```

### Step 2.2 — Verify with CLI

```bash
aws ec2 describe-vpcs \
  --filters "Name=tag:Name,Values=console-lab-vpc" \
  --query 'Vpcs[0].{VpcId:VpcId,Cidr:CidrBlock,DnsHostnames:EnableDnsHostnames}' \
  --output table
```

**Validate** — `VpcId` starts with `vpc-`; CIDR is `10.99.0.0/16`.

Copy `VpcId` to your personal notes as `VPC_ID`.

---

## Exercise 3 — Create public subnet

<a id="ex3"></a>

### Step 3.1 — Create subnet

**VPC** → **Subnets** → **Create subnet**

| Setting | Value |
|---------|-------|
| VPC ID | `console-lab-vpc` |
| Subnet name | `console-lab-public-a` |
| Availability Zone | `us-east-1a` (or first AZ in your region) |
| IPv4 CIDR | `10.99.1.0/24` |

**Validate** — subnet appears in the correct VPC.

**What happened:** Maps to `aws_subnet` with `vpc_id = aws_vpc.this.id`.

### Step 3.2 — Verify subnet

```bash
aws ec2 describe-subnets \
  --filters "Name=tag:Name,Values=console-lab-public-a" \
  --query 'Subnets[0].{SubnetId:SubnetId,VpcId:VpcId,Cidr:CidrBlock,Az:AvailabilityZone}' \
  --output table
```

**Validate** — `VpcId` matches `VPC_ID` from Exercise 2.

Copy `SubnetId` as `SUBNET_ID`.

---

## Exercise 4 — Internet gateway

<a id="ex4"></a>

### Step 4.1 — Create and attach IGW

**VPC** → **Internet gateways** → **Create internet gateway**

- Name: `console-lab-igw`
- **Actions** → **Attach to VPC** → select `console-lab-vpc`

**Validate** — State shows `attached`.

**What happened:** `aws_internet_gateway` + `aws_internet_gateway_attachment` in Terraform.

### Step 4.2 — CLI verification

```bash
aws ec2 describe-internet-gateways \
  --filters "Name=tag:Name,Values=console-lab-igw" \
  --query 'InternetGateways[0].{IgwId:InternetGatewayId,Attachments:Attachments}' \
  --output json
```

**Validate** — attachment `State` is `available`; `VpcId` matches your VPC.

Copy `InternetGatewayId` as `IGW_ID`.

---

## Exercise 5 — Public route

<a id="ex5"></a>

### Step 5.1 — Add route to internet

**VPC** → **Route tables** → select the route table associated with `console-lab-public-a` (or main route table).

**Routes** → **Edit routes** → **Add route**:

| Destination | Target |
|-------------|--------|
| `0.0.0.0/0` | `console-lab-igw` |

**Validate** — route table shows `0.0.0.0/0` → igw.

**What happened:** `aws_route` on `aws_route_table`. Subnet must be **associated** with this route table (automatic for main RT or explicit association).

### Step 5.2 — Confirm subnet association

In the route table **Subnet associations** tab, confirm `console-lab-public-a` is listed.

**Validate** — subnet uses the route table with the IGW route.

---

## Exercise 6 — Security group

<a id="ex6"></a>

### Step 6.1 — Find your public IP

```bash
MY_IP=$(curl -s ifconfig.me)
echo "${MY_IP}/32"
```

**Validate** — dotted-quad IP with `/32` suffix.

### Step 6.2 — Create security group

**VPC** → **Security groups** → **Create**

| Setting | Value |
|---------|-------|
| Name | `console-lab-sg` |
| VPC | `console-lab-vpc` |
| Inbound SSH | TCP 22 from `${MY_IP}/32` |
| Outbound | All traffic to `0.0.0.0/0` (default) |

**Validate** — SSH source is **not** `0.0.0.0/0`.

**What happened:** Terraform `aws_security_group` with `ingress` and `egress` blocks (see Extended Lab 14 dynamic ingress).

### Step 6.3 — CLI describe

```bash
aws ec2 describe-security-groups \
  --filters "Name=group-name,Values=console-lab-sg" \
  --query 'SecurityGroups[0].{GroupId:GroupId,Ingress:IpPermissions}' \
  --output json
```

Copy `GroupId` as `SG_ID`.

---

## Exercise 7 — Document Terraform mapping

<a id="ex7"></a>

### Step 7.1 — Complete resource map

Create a personal file (do not commit):

```text
# Console Lab 01 — Resource Map
VPC_ID=vpc-xxxxxxxx
SUBNET_ID=subnet-xxxxxxxx
IGW_ID=igw-xxxxxxxx
SG_ID=sg-xxxxxxxx
REGION=us-east-1
```

### Step 7.2 — Match each ID to Terraform address

| ID variable | Future Terraform address example |
|-------------|----------------------------------|
| VPC_ID | `aws_vpc.this.id` |
| SUBNET_ID | `aws_subnet.public.id` |
| IGW_ID | `aws_internet_gateway.this.id` |
| SG_ID | `aws_security_group.ssh.id` |

**Validate** — you can explain each row without reading the console.

**What happened:** Terraform **state** will store these same ID strings after apply in later labs.

---

## Exercise 8 — Optional EC2 launch (console)

<a id="ex8"></a>

### Step 8.1 — Launch instance

**EC2** → **Launch instance**

| Setting | Value |
|---------|-------|
| Name | `console-lab-bastion` |
| AMI | Ubuntu 22.04 |
| Instance type | `t3.micro` |
| Network | `console-lab-vpc` / `console-lab-public-a` |
| Auto-assign public IP | Enable |
| Security group | `console-lab-sg` |
| Key pair | Your lab key |

**Validate** — instance state `running`.

### Step 8.2 — SSH test

```bash
ssh -i ~/.ssh/your-lab-key.pem ubuntu@<PUBLIC_IP>
```

**Validate** — shell prompt on instance. Type `exit`.

### Step 8.3 — Terminate instance

**EC2** → **Terminate** `console-lab-bastion`.

**Validate** — instance `terminated` before VPC cleanup.

**What happened:** EC2 must be gone before subnet/VPC deletion.

---

## Exercise 9 — Compare with Terraform module (read-only)

<a id="ex9"></a>

### Step 9.1 — Read Essentials Lab 07 module

```bash
cat ~/terraform-ansible-labs/terraform/essentials/labs/lab07-simple-module/modules/network/main.tf
```

**Validate** — file contains `aws_vpc` and `aws_subnet` only (no IGW).

**What happened:** Lab 07 is minimal. Your console VPC is richer (IGW + routes + SG). Capstone projects add IGW in Terraform.

### Step 9.2 — List differences

| Component | Console Lab 01 | Essentials Lab 07 |
|-----------|----------------|-------------------|
| VPC | Yes | Yes |
| Subnet | Yes | Yes |
| Internet GW | Yes | No |
| Public route | Yes | No |
| Security group | Yes | No |

**Validate** — you understand Lab 07 is a subset.

---

## Exercise 10 — Console cleanup

<a id="ex10"></a>

### Step 10.1 — Delete in dependency order

1. Terminate any remaining EC2 instances
2. **Detach and delete** internet gateway `console-lab-igw`
3. Delete subnet `console-lab-public-a`
4. Delete security group `console-lab-sg`
5. Delete VPC `console-lab-vpc`

**Validate** — each step succeeds without dependency errors.

### Step 10.2 — CLI confirmation

```bash
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=console-lab-vpc" --query 'Vpcs'
aws ec2 describe-security-groups --filters "Name=group-name,Values=console-lab-sg" --query 'SecurityGroups'
```

**Validate** — both return empty lists `[]`.

**What happened:** Same resources Terraform `destroy` would remove — but console deletion is manual.

---

## Key takeaways

- Console workflows teach dependency order Terraform automates
- Every console object maps to a Terraform resource type
- Public subnets need IGW + `0.0.0.0/0` route
- SSH ingress should be `/32`, never open to the world
- Delete dependencies before parents (instances → IGW → subnet → VPC)

## Done when

- [ ] `aws sts get-caller-identity` showed training account
- [ ] Created VPC, subnet, IGW, route, and security group
- [ ] Verified at least three resources with AWS CLI
- [ ] Documented ID-to-Terraform-type mapping
- [ ] Deleted all `console-lab-*` resources
- [ ] Compared console VPC to Lab 07 Terraform module

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `DependencyViolation` deleting VPC | ENI, IGW, or instance remains | Delete/terminate dependents first |
| Cannot attach IGW | Wrong region or VPC pending | Wait for VPC `available` |
| SSH timeout | SG allows wrong CIDR | Update to `curl -s ifconfig.me`/32 |
| Subnet has no internet | Missing route or IGW | Add `0.0.0.0/0` → IGW route |
| Wrong account | Profile mis-set | `export AWS_PROFILE=training` |
| CIDR overlap error | `10.99.0.0/16` exists | Choose unused CIDR or delete old VPC |

## Cleanup checklist

```bash
# Verify nothing remains
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=console-lab-vpc"
aws ec2 describe-internet-gateways --filters "Name=tag:Name,Values=console-lab-igw"
aws ec2 describe-subnets --filters "Name=tag:Name,Values=console-lab-public-a"
```

All queries should return `[]` or empty `Vpcs`/`Subnets` arrays.

## Next steps

- [Lab 02 — Validate only](lab02-validate-only.md)
- [Essentials Lab 07 — Simple module](../../essentials/labmanuals/lab07-simple-module.md)
- [Extended projects doc](../docs/projects/README.md)

---
*Terraform Extended · Lab 01 · Next: [lab02-validate-only](lab02-validate-only.md)*
