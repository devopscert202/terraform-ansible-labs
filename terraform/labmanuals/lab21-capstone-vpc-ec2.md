# Lab 21 — Capstone: VPC to public web server

| | |
|---|---|
| **Goal** | A working web page served from an EC2 instance in a VPC you built entirely with Terraform. |
| **Time** | 45–60 minutes |
| **Tier** | Advanced |
| **Files** | `terraform/labs/lab21-capstone-vpc-ec2/` |

## Overview

Every lab so far taught one piece: a provider, a variable, an output, a dynamic block. This
capstone assembles them into one root module that builds a complete, reachable network from
nothing. A **VPC** is your private network inside AWS, a **subnet** is a slice of it, and an
**internet gateway** is the door to the public internet. You will create all of it, launch an
instance that installs a web server on first boot, and curl the resulting public URL.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `aws_vpc` | Private 10.0.0.0/16 network | Free |
| `aws_internet_gateway` | Door to the public internet | Free |
| `aws_subnet` | Public 10.0.1.0/24 slice, auto-assigns public IPs | Free |
| `aws_route_table` | Sends 0.0.0.0/0 to the gateway | Free |
| `aws_route_table_association` | Binds that table to the subnet | Free |
| `aws_security_group` | Instance firewall: inbound 80 only, all outbound | Free |
| `aws_instance` | t3.micro Amazon Linux 2023 running httpd | **Billable** |
| `data.aws_ami` | Resolves the current AL2023 image | Free |
| `data.aws_availability_zones` | Reports the zones this account can use | Free |

Seven managed resources and two data sources. The instance is genuinely billable — destroy it
the moment you finish.

## Before you start

- [ ] [Lab 20 — remote state consumer](lab20-remote-state-consumer.md) completed
- [ ] AWS credentials exported and verified with `aws sts get-caller-identity` (Lab 00)
- [ ] `curl` available in your terminal
- [ ] Lab code at [`../labs/lab21-capstone-vpc-ec2/`](../labs/lab21-capstone-vpc-ec2/)

## Steps

### Step 1 — Enter the lab directory

```bash
cd terraform/labs/lab21-capstone-vpc-ec2
ls *.tf terraform.tfvars.example
```

**Expected output**

```text
main.tf			outputs.tf		terraform.tfvars.example
variables.tf
```

Resources in `main.tf`, typed inputs in `variables.tf`, the published contract in `outputs.tf` —
the layout from Lab 06.

### Step 2 — Review the inputs you can change

```bash
grep '^variable' variables.tf
```

**Expected output**

```text
variable "aws_region" {
variable "project" {
variable "vpc_cidr" {
variable "public_subnet_cidr" {
variable "instance_type" {
variable "ingress_ports" {
variable "allowed_cidr" {
```

Every one has a default, so the lab applies with no input at all. `allowed_cidr` is the one
worth changing. There is deliberately no `availability_zone` variable — Step 5 shows where the
zone comes from instead.

### Step 3 — Create your tfvars from the example

```bash
cp terraform.tfvars.example terraform.tfvars
grep allowed_cidr terraform.tfvars
```

**Expected output**

```text
allowed_cidr = "0.0.0.0/0"
```

`0.0.0.0/0` means every source address on the internet, and the security group opens port 80 to
all of them. That is acceptable for a public web server you destroy within the hour; it is not a
pattern to copy. In any account that is not a throwaway lab account, edit `terraform.tfvars` and
set `allowed_cidr` to `YOUR_IP/32` before you continue.

### Step 4 — Read how the security group is generated

`var.ingress_ports` is a `list(number)`, and the `dynamic "ingress"` block from Lab 12 expands it
into one `ingress` rule per port. The list holds port 80 and nothing else: the instance has no
key pair, no step in this lab logs into it, and an open port nobody uses is only an attack
surface. Open a port when a step needs it, not in advance.

```bash
grep -A 10 'dynamic "ingress"' main.tf
```

**Expected output**

```text
  dynamic "ingress" {
    for_each = var.ingress_ports
    content {
      description = "Inbound TCP ${ingress.value}"
      from_port   = ingress.value
      to_port     = ingress.value
      protocol    = "tcp"
      cidr_blocks = [var.allowed_cidr]
    }
  }
```

### Step 5 — Read where the availability zone comes from

A subnet lives in exactly one **availability zone** — one isolated datacentre group inside the
region. The zone is not written into the configuration:

```bash
grep -B 1 -A 3 'aws_availability_zones' main.tf
```

**Expected output**

```text
# account which zones it can actually use, then take the first.
data "aws_availability_zones" "available" {
  state = "available"
}

--
  cidr_block              = var.public_subnet_cidr
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true
```

Writing `availability_zone = "us-east-1a"` looks harmless and is the most common way this
capstone breaks in someone else's account. Zone *names* are mapped per AWS account, so
`us-east-1a` is different physical hardware for you than for the person next to you; a zone can
be missing from an account entirely, and a zone that exists can refuse a launch because it has
no capacity for the instance type. The data source asks the account which zones it can actually
use and returns them in order, so `names[0]` is always a zone that works here.

Ask the same question with the CLI to see what the data source reads:

```bash
aws ec2 describe-availability-zones --filters Name=state,Values=available \
  --query 'AvailabilityZones[].ZoneName' --output text
```

**Expected output**

```text
us-east-1a	us-east-1b	us-east-1c	us-east-1d	us-east-1e	us-east-1f
```

Your list may be shorter or start with a different zone.

### Step 6 — Initialise the working directory

```bash
terraform init
```

**Expected output**

```text
Initializing the backend...

Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.100.0...
- Installed hashicorp/aws v5.100.0 (signed by HashiCorp)

Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above.

Terraform has been successfully initialized!
```

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
formatted. If it lists a filename, run `terraform fmt` to rewrite it.

### Step 8 — Plan and confirm the resource count

```bash
terraform plan
```

**Expected output**

```text
data.aws_availability_zones.available: Reading...
data.aws_ami.al2023: Reading...
data.aws_availability_zones.available: Read complete after 2s [id=us-east-1]
data.aws_ami.al2023: Read complete after 3s [id=ami-02b3d83d84b07786d]

Terraform will perform the following actions:

  # aws_instance.web will be created
  + resource "aws_instance" "web" {
      + ami                         = "ami-02b3d83d84b07786d"
      + instance_type               = "t3.micro"
      + public_ip                   = (known after apply)
      ...
    }

  # aws_subnet.public will be created
  + resource "aws_subnet" "public" {
      + availability_zone           = "us-east-1a"
      + cidr_block                  = "10.0.1.0/24"
      + map_public_ip_on_launch     = true
      ...
    }

Plan: 7 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + public_ip = (known after apply)
  + vpc_id    = (known after apply)
  + web_url   = (known after apply)
```

Both data sources are read before the plan is drawn, which is why the AMI id and the zone appear
as concrete values rather than `(known after apply)`. Your AMI id will differ, and the zone is
whichever one your account lists first.

Seven resources: VPC, gateway, subnet, route table, association, security group, instance. The
data sources are not in the count — they read, they do not create.

### Step 9 — Confirm the AMI was resolved, not hardcoded

```bash
terraform console
```

Then at the prompt:

```text
> data.aws_ami.al2023.id
```

**Expected output**

```text
"ami-02b3d83d84b07786d"
```

Type `exit` to leave the console. Your ID will differ from the one above and will change over
time — that is the point of `most_recent = true` with a name filter.

### Step 10 — Apply

Terraform prints the same plan again and waits. Type `yes` at the prompt; nothing else is
accepted.

```bash
terraform apply
```

**Expected output**

```text
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value: yes

aws_vpc.this: Creating...
aws_vpc.this: Creation complete after 3s [id=vpc-0a1b2c3d4e5f67890]
aws_internet_gateway.this: Creation complete after 1s [id=igw-04f2a1c9b7e3d5601]
aws_subnet.public: Creation complete after 2s [id=subnet-07c3e9a1b5d8f2461]
aws_route_table.public: Creation complete after 2s [id=rtb-0d6b8f1a3c5e70942]
aws_security_group.web: Creation complete after 4s [id=sg-05e7c2a9d1b4f6803]
aws_route_table_association.public: Creation complete after 1s [id=rtbassoc-0b9...]
aws_instance.web: Still creating... [20s elapsed]
aws_instance.web: Creation complete after 32s [id=i-0c4a7e19d2b6f3805]

Apply complete! Resources: 7 added, 0 changed, 0 destroyed.
```

### Step 11 — Read the outputs

```bash
terraform output
```

**Expected output**

```text
public_ip = "54.221.19.204"
vpc_id = "vpc-0a1b2c3d4e5f67890"
web_url = "http://54.221.19.204"
```

`-raw` prints one value with no quotes, which is what you pipe into other commands:

```bash
terraform output -raw web_url
```

**Expected output**

```text
http://54.221.19.204
```

### Step 12 — Wait for user-data to finish

**This is the step people skip, and it is why the capstone looks broken when it is not.**
`terraform apply` returns as soon as AWS reports the instance *running*. At that moment the
`user_data` script has barely started: it still has to install httpd and start it. The instance
answers pings before it answers HTTP. Poll until it does, which normally takes 60–90 seconds:

```bash
until curl -s -o /dev/null -w '%{http_code}\n' --max-time 5 "$(terraform output -raw web_url)" | grep -q 200; do
  echo "waiting for httpd..."
  sleep 10
done
echo "web server is up"
```

**Expected output**

```text
waiting for httpd...
waiting for httpd...
waiting for httpd...
waiting for httpd...
waiting for httpd...
waiting for httpd...
web server is up
```

If the loop is still printing after five minutes, stop it with `Ctrl-C` and work through the
`## If something fails` table — at that point it is a real fault, not the boot delay.

### Step 13 — Curl the public URL

```bash
curl -s "$(terraform output -raw web_url)"
```

**Expected output**

```text
<h1>tflabs-capstone is live</h1>
```

That page was written by the `user_data` script on first boot. Open the same URL in a browser
to see it rendered.

### Step 14 — Inspect what Terraform is tracking

```bash
terraform state list
```

**Expected output**

```text
data.aws_ami.al2023
data.aws_availability_zones.available
aws_instance.web
aws_internet_gateway.this
aws_route_table.public
aws_route_table_association.public
aws_security_group.web
aws_subnet.public
aws_vpc.this
```

The request arrived because all five network pieces lined up: the gateway is attached, the route
table sends 0.0.0.0/0 to it, the association binds that table to the subnet, the subnet assigns
a public IP, and the security group allows port 80.

### Step 15 — Destroy

Terraform lists everything it will remove and waits for the same `yes` confirmation.

```bash
terraform destroy
```

**Expected output**

```text
Plan: 0 to add, 0 to change, 7 to destroy.

Do you really want to destroy all resources?
  Terraform will destroy all your managed infrastructure, as shown above.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value: yes

aws_instance.web: Destroying... [id=i-0c4a7e19d2b6f3805]
aws_instance.web: Destruction complete after 41s
aws_route_table_association.public: Destruction complete after 1s
aws_security_group.web: Destruction complete after 1s
aws_subnet.public: Destruction complete after 1s
aws_route_table.public: Destruction complete after 1s
aws_internet_gateway.this: Destruction complete after 12s
aws_vpc.this: Destruction complete after 1s

Destroy complete! Resources: 7 destroyed.
```

Destruction runs in reverse dependency order: the instance goes before the subnet that holds
it, and the VPC goes last.

## Done when

- [ ] `terraform apply` reports `7 added, 0 changed, 0 destroyed`
- [ ] `terraform output web_url` prints an `http://` address
- [ ] `curl "$(terraform output -raw web_url)"` returns the `is live` page
- [ ] `terraform state list` shows all seven resources plus both data sources
- [ ] `terraform destroy` reports `7 destroyed` and `terraform state list` then prints nothing

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `curl: (52) Empty reply` or `Connection refused` right after apply | **Expected.** `user_data` has not finished installing httpd | Wait — rerun the Step 12 poll loop. Give it 90 seconds before suspecting anything else |
| `curl` still failing after 5 minutes | Port 80 not open, or `allowed_cidr` excludes you | `terraform state show aws_security_group.web` and check the ingress rules |
| `curl` times out with no response at all | Route table not associated, so the subnet is private | `terraform state show aws_route_table_association.public` |
| `public_ip` output is empty | Subnet is not assigning public IPs | Confirm `map_public_ip_on_launch = true` on `aws_subnet.public` |
| `UnauthorizedOperation` on apply | Lab account policy boundary, not a bad key | Verify the identity with `aws sts get-caller-identity` |
| `InsufficientInstanceCapacity` or `Unsupported` on launch | The first zone has no `t3.micro` capacity right now | Change `names[0]` to `names[1]` on `aws_subnet.public` and re-apply |
| `Your query returned no results` on the AMI | Name filter or region mismatch | Confirm `aws_region = "us-east-1"` |
| `DependencyViolation` during destroy | Something created outside Terraform is using the VPC | Remove it in the console, then rerun `terraform destroy` |

## Cleanup

This lab leaves a running EC2 instance billing by the hour. Destroying it is not optional. If
you completed Step 15, confirm nothing survived; otherwise run `terraform destroy` first.

```bash
terraform state list          # must print nothing
rm -f terraform.tfvars
rm -rf .terraform terraform.tfstate*
```

## Next steps

- Deep dive: [docs/advanced/projects.md](../docs/advanced/projects.md)
- Visual: [Advanced tier page](../html/advanced.html)
- Concepts recap: [AWS primer and architecture diagram](../html/aws-primer.html)
- You have finished the track. Return to the [lab index](README.md).
