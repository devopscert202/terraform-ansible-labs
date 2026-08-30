# Lab 22 — EC2 with remote state in S3

| | |
|---|---|
| **Goal** | Rebuild the capstone web server, with its state stored and locked in S3 instead of on your laptop. |
| **Time** | 45–60 minutes |
| **Tier** | Advanced |
| **Files** | `terraform/labs/lab22-ec2-s3-backend/` |

## Overview

[Lab 10](lab10-capstone-vpc-ec2.md) built a VPC, a public subnet and an EC2 web server, and kept
the record of them in a `terraform.tfstate` file on disk. [Lab 17](lab17-s3-backend.md) moved a
single throwaway resource's state into S3. This lab puts the two together: the same infrastructure
as Lab 10, with the same S3 backend as Lab 17 underneath it.

**Nothing about the AWS topology changes.** The same seven resources are built — VPC, gateway,
subnet, route table, association, security group and instance — with the same CIDRs, the same
resolved availability zone and the same `user_data`. The only difference that matters is where the
state file lives: an object in an S3 bucket rather than a file next to your code. That single
change is what turns a configuration one person runs on one laptop into a configuration a team and
a CI pipeline can share, which is why it is worth a lab of its own.

Two details in the code do differ from Lab 10, and neither changes what AWS ends up holding. The
name prefix is `tflabs-remote` rather than `tflabs-capstone`, so the two labs' resources are
distinguishable if you ever run them side by side. And the security group's ingress rules come from
a `dynamic` block over a `list(number)` variable named `ingress_ports`, the technique you learned in
[Lab 21](lab21-dynamic-blocks.md), rather than Lab 10's single literal `ingress` block. With the
default `ingress_ports = [80]` the generated rule is identical to Lab 10's; the difference is only
that adding a second port here is a data change.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| S3 bucket, versioning enabled | Holds this lab's remote state | Free to create; a few kilobytes of state costs well under a cent per month |
| `aws_vpc` | Private 10.0.0.0/16 network | Free |
| `aws_internet_gateway` | Door to the public internet | Free |
| `aws_subnet` | Public 10.0.1.0/24 slice, auto-assigns public IPs | Free |
| `aws_route_table` | Sends 0.0.0.0/0 to the gateway | Free |
| `aws_route_table_association` | Binds that table to the subnet | Free |
| `aws_security_group` | Instance firewall: inbound 80 only, all outbound | Free |
| `aws_instance` | t3.micro Amazon Linux 2023 running httpd | **Billable — destroy it the moment you finish** |
| `data.aws_ami` | Resolves the current AL2023 image | Free |
| `data.aws_availability_zones` | Reports the zones this account can use | Free |

Seven managed resources and two data sources, plus one bucket you create with the AWS CLI.
Terraform cannot create the bucket that holds its own state — the backend must exist before `init`
can connect to it.

## Before you start

- [ ] [Lab 21 — Dynamic blocks](lab21-dynamic-blocks.md) completed
- [ ] Terraform 1.11.0 or newer, for generally-available `use_lockfile` (`terraform version`)
- [ ] AWS CLI version 2, and AWS credentials exported (see [Lab 00](lab00-aws-setup-and-init.md)) with `aws sts get-caller-identity` working
- [ ] `curl` available in your terminal
- [ ] Lab code at [`../labs/lab22-ec2-s3-backend/`](../labs/lab22-ec2-s3-backend/)

**You need a state bucket, and you almost certainly do not have one.** Labs 17, 18 and 19 shared a
bucket held in `TF_STATE_BUCKET`, and [Lab 19's cleanup](lab19-state-migration.md#cleanup) deleted
it. This lab therefore creates its own bucket in steps 5 to 8 and deletes it again in
[Cleanup](#cleanup) — it shares nothing with any other lab. If you skipped Lab 19's cleanup and
that bucket still exists, you may reuse it; export its name in step 5 instead of creating a new
one and skip straight to step 9. The `key` in `backend.hcl` is `labs/lab22/terraform.tfstate`, so
it will not collide with anything labs 17 to 19 left behind.

## Steps

### Step 1 — Enter the lab directory

```bash
cd terraform/labs/lab22-ec2-s3-backend
ls -1 *.tf *.example
```

**Expected output**

```text
backend.hcl.example
main.tf
outputs.tf
terraform.tfvars.example
variables.tf
```

`main.tf`, `variables.tf` and `outputs.tf` are Lab 10's build with the two changes noted in the
overview. `backend.hcl.example` is Lab 17's.

### Step 2 — Read the backend block

```bash
grep -B 2 -A 3 'backend "s3"' main.tf
```

**Expected output**

```text
  # Partial configuration: bucket, key, region and locking come from backend.hcl
  # at init time, because backend blocks cannot reference variables.
  backend "s3" {}
}
```

An empty `backend "s3" {}` is a **partial configuration**: the block declares which backend to use
and nothing else. Backend blocks are read before Terraform evaluates any expression, so
`bucket = var.bucket` is impossible. Account-specific values arrive at `init` time from a separate
file, which is why this lab has a `backend.hcl` rather than putting the bucket name in
`terraform.tfvars`.

### Step 3 — Confirm the raised version floor

```bash
grep -A 6 '^terraform {' main.tf
terraform version
```

**Expected output** *(your Terraform version will differ; it must be 1.11.0 or newer)*

```text
terraform {
  # Higher than the track's >= 1.5.0 floor, for the same reason as labs 17 to 19:
  # backend.hcl.example sets use_lockfile, experimental in 1.10 and generally
  # available from 1.11. A learner on 1.5 to 1.9 would pass this check and then
  # fail at init with "Unsupported argument: use_lockfile".
  required_version = ">= 1.11.0"
Terraform v1.14.8
on darwin_arm64
```

Locking uses `use_lockfile = true` — **native S3 locking**, where Terraform writes a small
`.tflock` object beside the state and a second apply refuses to start while it exists. Older
tutorials pair the S3 backend with a `dynamodb_table` argument; that argument is deprecated and
Terraform 1.14 warns about it, so do not add it. Native locking was experimental in 1.10 and is
generally available from 1.11, so the floor is raised here to fail early with a clear version
message instead of an obscure `Unsupported argument` at `init`.

### Step 4 — Validate before touching AWS

`-backend=false` tells `init` to skip connecting to S3, so you can check the HCL with no bucket and
no credentials.

```bash
terraform init -backend=false
terraform fmt -check
terraform validate
```

**Expected output** *(provider version may differ)*

```text
Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 5.0"...
- Installing hashicorp/aws v5.100.0...
- Installed hashicorp/aws v5.100.0 (signed by HashiCorp)

Terraform has been successfully initialized!
Success! The configuration is valid.
```

`terraform fmt -check` prints nothing and exits 0 when the files are already canonically formatted.

### Step 5 — Choose a globally unique bucket name

**S3 bucket names are globally unique across every AWS account in the world**, so you must invent
one. `tfstate-lab22-yourname-4821` below is a **placeholder, not a usable name** — copying it
verbatim either fails or puts your state in a bucket shared with every other reader. Replace
`yourname` with your own name or initials and `4821` with four digits of your own choosing. Names
are 3 to 63 characters, lowercase letters, digits, hyphens and dots only.

```bash
export TF_STATE_BUCKET="tfstate-lab22-yourname-4821"
echo "$TF_STATE_BUCKET"
```

**Expected output** *(yours will differ — that is the point)*

```text
tfstate-lab22-yourname-4821
```

The variable lives only in this terminal. If you open a new one, re-export it.

### Step 6 — Create the state bucket

```bash
aws s3api create-bucket --bucket "$TF_STATE_BUCKET" --region us-east-2 \
  --create-bucket-configuration LocationConstraint=us-east-2
```

**Expected output** *(yours will differ)*

```text
{
    "Location": "http://tfstate-lab22-yourname-4821.s3.amazonaws.com/",
    "BucketArn": "arn:aws:s3:::tfstate-lab22-yourname-4821"
}
```

Every region except `us-east-1` requires `--create-bucket-configuration`, because `us-east-1` is
the S3 API's default location and any other region must be named explicitly. Omitting it in
`us-east-2` fails with:

```text
An error occurred (IllegalLocationConstraintException) when calling the CreateBucket operation:
The unspecified location constraint is incompatible for the region specific endpoint this request
was sent to.
```

### Step 7 — Enable versioning

Terraform overwrites the whole state object on every apply. **Versioning** keeps every prior copy,
so a truncated write or an accidental `state rm` is recoverable. New buckets have it off.

```bash
aws s3api put-bucket-versioning --bucket "$TF_STATE_BUCKET" \
  --versioning-configuration Status=Enabled
aws s3api get-bucket-versioning --bucket "$TF_STATE_BUCKET"
```

**Expected output**

```text
{
    "Status": "Enabled"
}
```

`put-bucket-versioning` prints nothing on success; the `get-` call is the confirmation.

### Step 8 — Confirm the bucket is private

State holds resource attributes in plaintext, so a public state bucket is a leak. Buckets created
since April 2023 block public access by default — verify rather than assume.

```bash
aws s3api get-public-access-block --bucket "$TF_STATE_BUCKET"
```

**Expected output**

```text
{
    "PublicAccessBlockConfiguration": {
        "BlockPublicAcls": true,
        "IgnorePublicAcls": true,
        "BlockPublicPolicy": true,
        "RestrictPublicBuckets": true
    }
}
```

All four must be `true`. If any is `false`, set them with `aws s3api put-public-access-block`.

### Step 9 — Write your backend config file

`backend.hcl` carries real account values and is gitignored; only `backend.hcl.example` is tracked.
`encrypt = true` asserts server-side encryption for the state object.

```bash
cp backend.hcl.example backend.hcl
# Edit backend.hcl: set bucket to your own $TF_STATE_BUCKET name
cat backend.hcl
```

**Expected output** *(yours will differ)*

```text
bucket       = "tfstate-lab22-yourname-4821"
key          = "labs/lab22/terraform.tfstate"
region       = "us-east-2"
encrypt      = true
use_lockfile = true
```

The `key` is the object path inside the bucket. It is what keeps one bucket able to hold many
projects' states without collision.

### Step 10 — Initialize the real backend

```bash
terraform init -backend-config=backend.hcl
```

**Expected output**

```text
Initializing the backend...

Successfully configured the backend "s3"! Terraform will automatically
use this backend unless the backend configuration changes.

Initializing provider plugins...
- Using previously-installed hashicorp/aws v5.100.0

Terraform has been successfully initialized!
```

### Step 11 — Create your tfvars

```bash
cp terraform.tfvars.example terraform.tfvars
grep -E 'ingress_ports|allowed_cidr' terraform.tfvars
```

**Expected output**

```text
ingress_ports      = [80]
allowed_cidr       = "0.0.0.0/0"
```

`0.0.0.0/0` opens port 80 to every address on the internet. Acceptable for a public web server you
destroy within the hour; in any account that is not a throwaway lab account, set it to `YOUR_IP/32`
first. Port 80 is the only port opened — the instance has no key pair and no step here logs into
it.

`ingress_ports` is a `list(number)` with one element, and the security group expands it with a
`dynamic "ingress"` block:

```bash
grep -A 9 'dynamic "ingress"' main.tf
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

One element in the list means one generated `ingress` block, which is why the plan in Step 13 shows
the same single rule Lab 10 wrote out by hand. Iterating a list rather than a map, `ingress.value`
is the element itself — the port number — not an object.

### Step 12 — Confirm the zone is resolved, not hardcoded

```bash
grep -A 1 'availability_zone  ' main.tf
aws ec2 describe-availability-zones --filters Name=state,Values=available \
  --query 'AvailabilityZones[].ZoneName' --output text
```

**Expected output**

```text
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true
us-east-2a	us-east-2b	us-east-2c
```

Zone *names* are mapped per account, so `us-east-2a` is different physical hardware for you than
for the person next to you, and a named zone can be absent or out of capacity. The data source asks
the account which zones it can actually use and returns them in order.

### Step 13 — Plan

```bash
terraform plan
```

**Expected output** *(trimmed; AMI id and zone will differ)*

```text
data.aws_ami.al2023: Reading...
data.aws_availability_zones.available: Reading...
data.aws_availability_zones.available: Read complete after 2s [id=us-east-2]
data.aws_ami.al2023: Read complete after 2s [id=ami-01042494dba64ab96]

  # aws_instance.web will be created
  + resource "aws_instance" "web" {
      + ami                                  = "ami-01042494dba64ab96"
      + instance_type                        = "t3.micro"
      ...
    }

  # aws_subnet.public will be created
  + resource "aws_subnet" "public" {
      + availability_zone                              = "us-east-2a"
      + cidr_block                                     = "10.0.1.0/24"
      ...
    }

Plan: 7 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + public_ip = (known after apply)
  + vpc_id    = (known after apply)
  + web_url   = (known after apply)

Releasing state lock. This may take a few moments...
```

Seven resources — VPC, gateway, subnet, route table, association, security group, instance —
exactly Lab 10's count. Data sources read, they do not create, so they are not counted. The
`Releasing state lock` line at the end is new: a remote backend locks for `plan` as well as
`apply`, because both read state.

### Step 14 — Apply

```bash
terraform apply -auto-approve
```

**Expected output** *(trimmed; ids and IP will differ)*

```text
aws_vpc.this: Creating...
aws_vpc.this: Creation complete after 14s [id=vpc-0a16778b2e9f88c25]
aws_internet_gateway.this: Creation complete after 2s [id=igw-0ea766f1759e412f2]
aws_route_table.public: Creation complete after 3s [id=rtb-0273b2a11217f7b9b]
aws_security_group.web: Creation complete after 5s [id=sg-0a2dc473a1105fd6c]
aws_subnet.public: Creation complete after 13s [id=subnet-094ec3902ccfcec70]
aws_route_table_association.public: Creation complete after 1s [id=rtbassoc-0316d0db7fa3c754d]
aws_instance.web: Creating...
aws_instance.web: Creation complete after 15s [id=i-0f3922bc72788c323]
Releasing state lock. This may take a few moments...

Apply complete! Resources: 7 added, 0 changed, 0 destroyed.

Outputs:

public_ip = "3.17.179.98"
vpc_id = "vpc-0a16778b2e9f88c25"
web_url = "http://3.17.179.98"
```

The matching `Acquiring state lock` line is printed only when the acquire is slow enough to be
worth reporting, so on an uncontended bucket you usually see only the release.

### Step 15 — Confirm there is no local state file

```bash
ls terraform.tfstate
```

**Expected output**

```text
ls: terraform.tfstate: No such file or directory
```

The missing file is the whole point. Lose this laptop and the record of these seven resources is
unaffected, because it was never here.

### Step 16 — Find the state object in S3

```bash
aws s3 ls "s3://$TF_STATE_BUCKET/labs/lab22/"
```

**Expected output** *(timestamp and size will differ)*

```text
2026-08-30 17:18:39      19613 terraform.tfstate
```

That object is the single source of truth. A teammate who exports the same bucket name, copies the
same `backend.hcl` and runs `terraform init` sees these exact seven resources and will not
re-create them.

### Step 17 — See the lock objects in the version history

```bash
aws s3api list-object-versions --bucket "$TF_STATE_BUCKET" \
  --query 'Versions[].{Key:Key,Size:Size}' --output table
```

**Expected output** *(row count depends on how many plans you ran)*

```text
--------------------------------------------------
|               ListObjectVersions               |
+---------------------------------------+--------+
|                  Key                  | Size   |
+---------------------------------------+--------+
|  labs/lab22/terraform.tfstate         |  19613 |
|  labs/lab22/terraform.tfstate         |  19450 |
|  labs/lab22/terraform.tfstate.tflock  |  244   |
|  labs/lab22/terraform.tfstate.tflock  |  243   |
|  labs/lab22/terraform.tfstate.tflock  |  243   |
+---------------------------------------+--------+
```

Two things are visible here, and they are the two things remote state buys you beyond durability.
Multiple `terraform.tfstate` versions are the history versioning preserved — every apply's previous
state is still fetchable. The `.tflock` entries are `use_lockfile` at work: each `plan` and `apply`
wrote that object at the start and deleted it at the end, and while it existed a second person
running `apply` against this bucket would have been refused rather than allowed to overwrite your
state concurrently.

### Step 18 — Wait for user-data to finish

`terraform apply` returns as soon as AWS reports the instance *running*, which is before
`user_data` has installed httpd. The instance answers pings before it answers HTTP.

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
web server is up
```

If the loop is still printing after five minutes, work through the `If something fails` table.

### Step 19 — Curl the public URL

```bash
curl -si "$(terraform output -raw web_url)" | head -3
curl -s "$(terraform output -raw web_url)"
```

**Expected output** *(date will differ)*

```text
HTTP/1.1 200 OK
Date: Sun, 30 Aug 2026 11:49:30 GMT
Server: Apache/2.4.68 (Amazon Linux)
<h1>tflabs-remote is live, state in S3</h1>
```

A real web page, served over the public internet, from infrastructure whose state Terraform read
out of S3 rather than off this disk.

### Step 20 — Read state through the remote backend

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

No flags, no local file — the CLI fetched the object from S3 to answer this.

## Done when

- [ ] `terraform init -backend-config=backend.hcl` reported the backend configured
- [ ] `terraform apply` reported `7 added, 0 changed, 0 destroyed`
- [ ] No `terraform.tfstate` exists locally
- [ ] `aws s3 ls "s3://$TF_STATE_BUCKET/labs/lab22/"` lists the state object
- [ ] `list-object-versions` shows more than one state version and at least one `.tflock` entry
- [ ] `curl "$(terraform output -raw web_url)"` returns the `is live, state in S3` page
- [ ] `terraform state list` shows seven resources plus two data sources
- [ ] You can state what changed from Lab 10 (only where state lives) and what did not (the resources)

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `Backend initialization required, please run "terraform init"` on `plan` | Only `init -backend=false` has been run | Run step 10 |
| `NoSuchBucket` at `init` | Step 6 skipped, `backend.hcl` still holds the placeholder, or the name is mistyped | `aws s3 ls "s3://$TF_STATE_BUCKET"`, then check `bucket` in `backend.hcl` matches exactly |
| `IllegalLocationConstraintException` on `create-bucket` | `--create-bucket-configuration` omitted outside `us-east-1` | Add `LocationConstraint=us-east-2` as in step 6 |
| `BucketAlreadyExists` | Someone else in AWS owns that name | Pick a different name, re-export `TF_STATE_BUCKET`, retry |
| `BucketAlreadyOwnedByYou` | You already created it | Nothing to fix; continue at step 7 |
| `InvalidBucketName` | Uppercase letters or underscores | Lowercase letters, digits, hyphens and dots only, 3–63 characters |
| `Unsupported argument: use_lockfile` | Terraform older than 1.10 | Upgrade to 1.11 or newer |
| `Unsupported Terraform Core version` | Terraform older than `>= 1.11.0` | Upgrade Terraform; do not lower `required_version` |
| `Error acquiring the state lock` | A previous run died mid-apply, or a teammate is applying | Confirm nobody is applying, then `terraform force-unlock <LOCK_ID>` |
| `Backend configuration changed` | `backend.hcl` edited after init | `terraform init -reconfigure`, or `-migrate-state` to move the state |
| `No valid credential sources found` | No AWS credentials exported | Export keys as in Lab 00; backends ignore the provider block's `profile` |
| `curl: (52) Empty reply` or `Connection refused` right after apply | **Expected.** `user_data` has not finished | Rerun the step 18 poll loop; allow 90 seconds |
| `curl` still failing after 5 minutes | Port 80 closed, or `allowed_cidr` excludes you | `terraform state show aws_security_group.web` |
| `curl` times out with no response | Route table not associated, so the subnet is private | `terraform state show aws_route_table_association.public` |
| `InsufficientInstanceCapacity` on launch | The first zone has no `t3.micro` capacity now | Change `names[0]` to `names[1]` on `aws_subnet.public` and re-apply |
| `DependencyViolation` during destroy | Something created outside Terraform is using the VPC | Remove it in the console, then rerun `terraform destroy` |
| `BucketNotEmpty` on `delete-bucket` | Object versions or delete markers remain | Run the full four-command sequence in Cleanup, in order |

## Cleanup

Two things must go: the billable infrastructure, and this lab's bucket. No later lab uses either.

Destroy the infrastructure first, while the state is still readable.

```bash
terraform destroy -auto-approve
terraform state list          # must print nothing
```

**Expected output** *(trimmed)*

```text
Plan: 0 to add, 0 to change, 7 to destroy.
aws_instance.web: Destruction complete after 32s
aws_route_table_association.public: Destruction complete after 1s
aws_security_group.web: Destruction complete after 2s
aws_subnet.public: Destruction complete after 1s
aws_route_table.public: Destruction complete after 2s
aws_internet_gateway.this: Destruction complete after 1s
aws_vpc.this: Destruction complete after 1s
Releasing state lock. This may take a few moments...

Destroy complete! Resources: 7 destroyed.
```

**A versioned bucket cannot be deleted until every object version is gone.** `aws s3 rm --recursive`
is not enough: it deletes the *current* version of each object by writing a delete marker, leaving
the old versions and the markers behind, and `delete-bucket` then refuses with
`BucketNotEmpty`. Run all four commands in order, in the terminal where `TF_STATE_BUCKET` is
exported.

```bash
aws s3 rm "s3://$TF_STATE_BUCKET" --recursive

aws s3api delete-objects --bucket "$TF_STATE_BUCKET" --delete "$(
  aws s3api list-object-versions --bucket "$TF_STATE_BUCKET" --output json \
    --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}')"

aws s3api delete-objects --bucket "$TF_STATE_BUCKET" --delete "$(
  aws s3api list-object-versions --bucket "$TF_STATE_BUCKET" --output json \
    --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}')"

aws s3api delete-bucket --bucket "$TF_STATE_BUCKET"
```

**Expected output** *(keys and version ids will differ; `delete-bucket` prints nothing)*

```text
delete: s3://tfstate-lab22-yourname-4821/labs/lab22/terraform.tfstate
{
    "Deleted": [
        {
            "Key": "labs/lab22/terraform.tfstate.tflock",
            "VersionId": "m3Py9PZpQ92aIqsSvG2aOMkwe_Trv_cB"
        },
        {
            "Key": "labs/lab22/terraform.tfstate",
            "VersionId": "cCnvO0teiWrLnnYq6E7RsUxkkT00mSVu"
        }
    ]
}
{
    "Deleted": [
        {
            "Key": "labs/lab22/terraform.tfstate",
            "VersionId": "2RcM40fBQ5yHgzCAZAeRBRQLCjhahZYs",
            "DeleteMarker": true,
            "DeleteMarkerVersionId": "2RcM40fBQ5yHgzCAZAeRBRQLCjhahZYs"
        }
    ]
}
```

If a category is already empty the query returns no list and the CLI rejects the call locally with
`Invalid type for parameter Delete.Objects, value: None` — that is the "nothing to delete" signal,
so continue to `delete-bucket`.

Confirm the bucket is gone and remove the local artefacts.

```bash
aws s3 ls "s3://$TF_STATE_BUCKET"
rm -f backend.hcl terraform.tfvars
rm -rf .terraform
```

**Expected output**

```text
An error occurred (NoSuchBucket) when calling the ListObjectsV2 operation: The specified bucket
does not exist
```

The error is the success condition. Finally check that no instance survived:

```bash
aws ec2 describe-instances --filters Name=tag:Lab,Values=lab22 \
  --query 'Reservations[].Instances[].[InstanceId,State.Name]' --output text
```

**Expected output** *(a terminated instance stays listed for about an hour and is not billed; `running` is not acceptable)*

```text
i-0f3922bc72788c323	terminated
```

## Next steps

- Deep dive: [../docs/13-remote-state.md](../docs/13-remote-state.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab22-ec2-s3-backend)
- Continue to [Lab 23 — S3 bucket as a Terraform resource](lab23-s3-bucket.md)
