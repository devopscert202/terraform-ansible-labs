# Lab 15 — remote-exec provisioner

| | |
|---|---|
| **Goal** | Build an SSH-reachable EC2 target, then run a command on it over SSH from inside `terraform apply`, verifying each of the five environmental conditions that must hold for it to work. |
| **Time** | 50–65 minutes |
| **Tier** | Advanced |
| **Files** | `terraform/labs/lab15-remote-exec-provisioner/` |

## Overview

`remote-exec` is the sibling of `local-exec` from lab 14. Instead of running a command on your
own machine, it opens an **SSH** connection to a server and runs the command there. SSH (Secure
Shell) is the standard encrypted remote-login protocol; it listens on TCP port 22.

Provisioners are still a last resort, and `remote-exec` is the worst offender. It only works if
five separate things are all true at the exact moment Terraform runs: the instance is up, it has
a reachable public address, the firewall permits port 22 from you, the private key file is
correct and correctly permissioned, and the login name matches the operating system image. Any
one of them being wrong fails the apply and leaves the resource marked `tainted`. Production
teams use EC2 user-data, AWS Systems Manager Run Command, or a pre-baked image instead.

This is the lab most likely to fail for reasons that have nothing to do with your Terraform
code. Steps 3 to 5 build the target — a key pair, a firewall rule for your own address, and the
instance itself — and steps 6 to 11 then verify the five conditions one at a time, before
Terraform is involved at all. Work through them in order and do not skip ahead: a failure caught
by `ssh` is far easier to read than the same failure caught by a provisioner.

**A note on the expected output below.** The Terraform `validate` and `plan` blocks and the AWS
CLI blocks in steps 3 to 6 were captured from a real run in `us-east-2`. The `ssh` and
`remote-exec` handshake blocks depend on your account, network, and instance, so they are marked
*(yours will differ)* and show the documented shape.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `terraform_data.bootstrap` | Holds the target hostname and carries the `connection` block | Free |
| `remote-exec` provisioner | Runs `echo ... $(hostname)` over SSH on the target | Free |
| Output `target` | Echoes the host you connected to | Free |

The Terraform module here does **not** create the EC2 instance. You supply a host that already
exists, and steps 3 to 5 create one with the AWS CLI. Building the target outside Terraform is
deliberate: it keeps the provisioner's five conditions as the only thing this lab is testing.

These three AWS objects are created in steps 3 to 5 and removed in cleanup:

| Object | Purpose | Cost |
|---|---|---|
| EC2 key pair `lab-key` | The SSH identity the instance will trust | Free |
| Security group `lab15-ssh` | Allows TCP 22 inbound from your address only | Free |
| `t3.micro` Amazon Linux 2023 instance | The host the provisioner connects to | **Billed per second while running** |

The instance is the only billable item. Complete the lab in one sitting and run the cleanup.

## Before you start

- [ ] [Lab 14 — local-exec provisioner](lab14-local-exec-provisioner.md) completed
- [ ] The AWS CLI configured and verified — `aws sts get-caller-identity` returns your account,
      as set up in [Lab 00](lab00-aws-setup-and-init.md)
- [ ] A default VPC in `us-east-2`. Check with
      `aws ec2 describe-vpcs --filters Name=isDefault,Values=true --query 'Vpcs[].VpcId' --output text`.
      If that prints nothing, run `aws ec2 create-default-vpc` once
- [ ] Outbound TCP 22 permitted from your network. Many corporate networks block it; see the
      first row of [If something fails](#if-something-fails) for how that failure looks
- [ ] Read [../docs/11-provisioners.md](../docs/11-provisioners.md)

## Steps

### Step 1 — Move into the lab directory

```bash
cd terraform/labs/lab15-remote-exec-provisioner
ls
```

**Expected output**

```text
main.tf
terraform.tfvars.example
```

### Step 2 — Read the connection block

The `connection` block tells the provisioner *how* to reach the host, and is separate from the
provisioner that says *what* to run. `file(pathexpand(...))` reads the key from disk and expands
a leading `~` to your home directory.

```bash
grep -A7 'connection {' main.tf
```

**Expected output**

```text
  connection {
    type        = "ssh"
    host        = var.host
    user        = var.user
    private_key = file(pathexpand(var.private_key_path))
  }
  provisioner "remote-exec" {
    inline = ["echo Terraform remote-exec connected to $(hostname)"]
```

### Step 3 — Create an EC2 key pair

An **EC2 key pair** is an SSH keypair where AWS keeps the public half and installs it on any
instance you launch with that key name. You get the private half exactly once, at creation — AWS
cannot re-issue it, so a lost `.pem` means the instance is unreachable forever.

`--query 'KeyMaterial' --output text` extracts just the private key body, and the redirect writes
it straight to a file. Never let this file into git.

```bash
mkdir -p ~/.ssh
aws ec2 create-key-pair --key-name lab-key \
  --query 'KeyMaterial' --output text > ~/.ssh/lab-key.pem
aws ec2 describe-key-pairs --key-names lab-key \
  --query 'KeyPairs[].[KeyName,KeyType,KeyFingerprint]' --output table
```

**Expected output** *(your fingerprint will differ)*

```text
-------------------------------------------------------------------------------
|                              DescribeKeyPairs                               |
+---------+------+------------------------------------------------------------+
|  lab-key|  rsa |  b8:10:75:22:0a:d7:0f:af:40:25:b3:ce:2a:39:a6:ad:5f:8a:f4:de|
+---------+------+------------------------------------------------------------+
```

The file is 1675 bytes and begins `-----BEGIN RSA PRIVATE KEY-----`. If it contains anything
else — an error message, or nothing — the command failed and the key pair may still exist in AWS;
delete it with `aws ec2 delete-key-pair --key-name lab-key` and retry.

### Step 4 — Create a security group allowing SSH from your address only

A **security group** is the instance's firewall. It denies all inbound traffic unless a rule
allows it. `0.0.0.0/0` on port 22 would expose the instance to the entire internet, so scope the
rule to your own address with `/32`.

```bash
MYIP=$(curl -s https://checkip.amazonaws.com)
VPC=$(aws ec2 describe-vpcs --filters Name=isDefault,Values=true \
  --query 'Vpcs[0].VpcId' --output text)
SG=$(aws ec2 create-security-group --group-name lab15-ssh \
  --description "Lab 15 SSH from my address" --vpc-id "$VPC" \
  --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id "$SG" \
  --protocol tcp --port 22 --cidr "${MYIP}/32" \
  --query 'SecurityGroupRules[].[SecurityGroupRuleId,IpProtocol,FromPort,CidrIpv4]' \
  --output text
echo "SG=$SG  MYIP=$MYIP"
```

**Expected output** *(your ids and address will differ)*

```text
sgr-0609448a5a72fa724	tcp	22	134.231.215.172/32
SG=sg-0173f44ff75200942  MYIP=134.231.215.172
```

If `VPC` printed `None`, you have no default VPC — run `aws ec2 create-default-vpc` and repeat.
Keep this shell open; `$SG` is used in the next step. Note that your public address can change
if you reconnect or switch networks, which invalidates this rule.

### Step 5 — Launch the target instance

`data "aws_ami"` is how Terraform resolves an image, but this instance is being created outside
Terraform, so look the AMI up with the CLI using the same filter the labs use. Never hardcode an
AMI id: they are region-specific and are replaced with every new image release.

```bash
AMI=$(aws ec2 describe-images --owners amazon \
  --filters 'Name=name,Values=al2023-ami-2023.*-kernel-6.12-x86_64' \
  --query 'reverse(sort_by(Images,&CreationDate))[0].ImageId' --output text)
aws ec2 run-instances --image-id "$AMI" --instance-type t3.micro \
  --key-name lab-key --security-group-ids "$SG" \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=lab15-target},{Key=Lab,Value=lab15}]' \
  --query 'Instances[].[InstanceId,InstanceType,State.Name]' --output text
```

**Expected output** *(your instance id will differ)*

```text
i-0874d15af0a497f8f	t3.micro	pending
```

`pending` means AWS accepted the request; the operating system has not booted yet. Wait for both
status checks to report `ok` before attempting SSH — `sshd` is not listening until then, which
produces `Connection refused` if you rush it.

```bash
aws ec2 wait instance-status-ok --instance-ids i-0874d15af0a497f8f
```

This command prints nothing and returns when the instance is ready, typically 60 to 90 seconds.

### Step 6 — Condition 1: confirm the instance is running and note its public IP

An instance in `stopped` or `pending` state has no working `sshd`, and one without a public IP
cannot be reached from your laptop at all.

```bash
aws ec2 describe-instances \
  --filters 'Name=instance-state-name,Values=running' \
  --query 'Reservations[].Instances[].{ID:InstanceId,IP:PublicIpAddress,Key:KeyName,SG:SecurityGroups[0].GroupId}' \
  --output table
```

**Expected output** *(yours will differ)*

```text
------------------------------------------------------------------
|                       DescribeInstances                        |
+----------------------+----------------+----------+-------------+
|          ID          |       IP       |   Key    |     SG      |
+----------------------+----------------+----------+-------------+
|  i-0abc123def4567890 |  203.0.113.10  | lab-key  | sg-0a1b2c3d |
+----------------------+----------------+----------+-------------+
```

Record the `IP`, `Key`, and `SG` values — the next three steps each use one of them. If `IP` is
blank, the instance is in a private subnet and `remote-exec` cannot reach it from here.

On a narrow terminal the AWS CLI prints this table rotated, one field per row, rather than in
columns. The values are the same.

### Step 7 — Condition 2: confirm the security group allows port 22 from your address

A **security group** is the instance's firewall. It denies everything unless a rule allows it, so
a missing port 22 ingress rule is the single most common cause of the timeout in step 11.

```bash
curl -s https://checkip.amazonaws.com
aws ec2 describe-security-groups --group-ids sg-0a1b2c3d \
  --query 'SecurityGroups[].IpPermissions[?FromPort==`22`]' --output json
```

**Expected output** *(yours will differ)*

```text
198.51.100.24
[
    [
        {
            "FromPort": 22,
            "IpProtocol": "tcp",
            "IpRanges": [ { "CidrIp": "198.51.100.24/32" } ],
            "ToPort": 22
        }
    ]
]
```

An empty `[]` means no rule for port 22 exists. Add one for your address before continuing.

### Step 8 — Condition 3: confirm your key file matches the instance's key pair

The `Key` column from step 6 names the key pair the instance was launched with. Only the private
key from *that* pair will authenticate; a different `.pem` fails with `Permission denied`.

```bash
ls -l ~/.ssh/lab-key.pem
```

**Expected output** *(yours will differ)*

```text
-rw-r--r--@ 1 you  staff  1675 Aug 29 11:20 /Users/you/.ssh/lab-key.pem
```

### Step 9 — Condition 4: restrict the private key's permissions

SSH refuses to use a key that other users on the machine can read, and reports
`UNPROTECTED PRIVATE KEY FILE`. `chmod 400` makes it read-only to you alone.

```bash
chmod 400 ~/.ssh/lab-key.pem
ls -l ~/.ssh/lab-key.pem
```

**Expected output** *(yours will differ)*

```text
-r--------@ 1 you  staff  1675 Aug 29 11:20 /Users/you/.ssh/lab-key.pem
```

The leading `-r--------` is what you are checking for. Anything with `r` in the group or other
positions will be rejected.

### Step 10 — Condition 5: confirm the login name for your image

Amazon Linux 2023 logs in as `ec2-user`. Ubuntu uses `ubuntu`, Debian uses `admin`, and `root`
is disabled on all of them. Using the wrong name fails with `Permission denied (publickey)`,
which looks identical to a wrong-key error.

```bash
ssh -i ~/.ssh/lab-key.pem ec2-user@203.0.113.10 'whoami'
```

**Expected output** *(yours will differ)*

```text
ec2-user
```

### Step 11 — Prove SSH works end to end before involving Terraform

This is the same command the provisioner will run. If it works here, the five conditions hold.

```bash
ssh -i ~/.ssh/lab-key.pem ec2-user@203.0.113.10 'hostname'
```

**Expected output** *(yours will differ)*

```text
ip-10-0-1-42.us-east-2.compute.internal
```

If this hangs for about a minute and then times out, return to step 7 — the security group is
blocking you. Do not continue until this command succeeds.

### Step 12 — Supply your values

`private_key_path` is marked `sensitive = true`, so Terraform will not print it in plan or apply
output. `terraform.tfvars` holds real values and must never be committed.

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: set host to your public IP from step 6
cat terraform.tfvars
```

**Expected output** *(yours will differ)*

```text
host             = "203.0.113.10"
user             = "ec2-user"
private_key_path = "~/.ssh/lab-key.pem"
```

### Step 13 — Initialize

```bash
terraform init
```

**Expected output**

```text
Initializing provider plugins...
- terraform.io/builtin/terraform is built in to Terraform

Terraform has been successfully initialized!
```

### Step 14 — Validate the configuration

```bash
terraform validate
```

**Expected output**

```text
Success! The configuration is valid.
```

### Step 15 — Plan

```bash
terraform plan
```

**Expected output**

```text
Terraform will perform the following actions:

  # terraform_data.bootstrap will be created
  + resource "terraform_data" "bootstrap" {
      + id     = (known after apply)
      + input  = "203.0.113.10"
      + output = (known after apply)
    }

Plan: 1 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + target = (known after apply)
```

As in lab 14, the plan says nothing about the SSH command or the connection — Terraform cannot
preview either. Note that `private_key_path` does not appear anywhere, because it is `sensitive`.

### Step 16 — Apply and watch the SSH handshake

```bash
terraform apply -auto-approve
```

**Expected output** *(yours will differ)*

```text
terraform_data.bootstrap: Creating...
terraform_data.bootstrap: Provisioning with 'remote-exec'...
terraform_data.bootstrap (remote-exec): Connecting to remote host via SSH...
terraform_data.bootstrap (remote-exec):   Host: 203.0.113.10
terraform_data.bootstrap (remote-exec):   User: ec2-user
terraform_data.bootstrap (remote-exec):   Private key: true
terraform_data.bootstrap (remote-exec): Connected!
terraform_data.bootstrap (remote-exec): Terraform remote-exec connected to ip-10-0-1-42.us-east-2.compute.internal

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

target = "203.0.113.10"
```

Terraform retries the connection for several minutes before giving up, so a failure here is slow.
The internal hostname reflects your instance's private IP.

### Step 17 — Read the output back

```bash
terraform output target
```

**Expected output** *(yours will differ)*

```text
"203.0.113.10"
```

## Done when

- [ ] `~/.ssh/lab-key.pem` exists, is 1675 bytes, and starts `-----BEGIN RSA PRIVATE KEY-----`
- [ ] The security group's only inbound rule is TCP 22 from your address with a `/32` mask
- [ ] `aws ec2 wait instance-status-ok` returned before you attempted SSH
- [ ] The instance showed as `running` with a public IP in step 6
- [ ] A port 22 ingress rule for your address exists in step 7
- [ ] `ls -l` shows `-r--------` on the private key after step 9
- [ ] `ssh ... 'whoami'` returned `ec2-user` in step 10
- [ ] Plain `ssh ... 'hostname'` reached the host in step 11
- [ ] `terraform apply` printed `Connected!` followed by the remote hostname
- [ ] `terraform.tfvars` exists locally and is not staged for commit
- [ ] You can explain why user-data or SSM would be the better tool here

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `Connection timed out during banner exchange`, while the instance reports `ok`/`ok` and the security group already allows your exact address | Your own network blocks outbound TCP 22. A middlebox completes the TCP handshake, then drops the SSH protocol — which is why this is not a plain connect timeout | Not fixable from AWS; the security group is not at fault. Use a network that permits outbound 22, or substitute AWS Systems Manager Session Manager. This is common on corporate networks and is the single most likely reason this lab fails for you |
| `InvalidKeyPair.Duplicate: The keypair already exists` in step 3 | A `lab-key` key pair remains from an earlier attempt | AWS cannot re-issue the private half, so the old pair is useless without its `.pem`. Delete and recreate: `aws ec2 delete-key-pair --key-name lab-key`, then redo step 3 |
| `VPCIdNotSpecified: No default VPC for this user` in step 5 | The account has no default VPC, so `run-instances` has no subnet to place the instance in | Run `aws ec2 create-default-vpc` once, then redo step 4 (the `$VPC` lookup) and step 5 |
| `Connection refused` immediately in step 10 or 11 | The instance is running but `sshd` has not started | Wait for the step 5 `aws ec2 wait instance-status-ok` command to return before attempting SSH |
| Hangs on `Connecting to remote host via SSH...` then `timeout - last error: dial tcp ...:22: i/o timeout` | Security group has no inbound rule for TCP 22 from your address | Redo step 7; add ingress for `$(curl -s https://checkip.amazonaws.com)/32` |
| Same timeout, but the security group is correct | Instance has no public IP, or sits in a private subnet with no internet gateway route | Redo step 6; use an instance in a public subnet with `associate_public_ip_address = true` |
| Timeout only from a new location | Your public IP changed, so the old ingress rule no longer matches | Re-run step 7 and update the rule |
| `Permission denied (publickey)` | Wrong login name for the image | Redo step 10. Amazon Linux 2023 and RHEL use `ec2-user`, Ubuntu uses `ubuntu`. Never `root` |
| `Permission denied (publickey)` with the right user | The `.pem` does not match the instance's key pair | Compare against the `Key` column from step 6 and use that pair's private key |
| `UNPROTECTED PRIVATE KEY FILE` or `bad permissions` | Key file is group- or world-readable | Redo step 9: `chmod 400 ~/.ssh/lab-key.pem` |
| `Invalid function argument: no file exists at "..."` | `private_key_path` is wrong, or `~` was quoted so it never expanded | Use the real path; `pathexpand` handles `~` only inside the variable's value |
| `ssh: handshake failed: ... unable to authenticate` | The key is protected by a passphrase | `remote-exec` cannot answer a passphrase prompt; use a key with none |
| `Connection refused` rather than a timeout | The instance is up but `sshd` has not started yet | Wait for `2/2 checks passed` in the console, then apply again |
| `Host key verification failed` | The IP was reused by a different instance | Remove the stale entry: `ssh-keygen -R 203.0.113.10` |
| Resource stuck `tainted` after a failed apply | The create-time provisioner exited non-zero | Fix the underlying condition, then apply again — Terraform replaces tainted resources |
| Apply succeeds but nothing is configured | `remote-exec` ran but the command did nothing useful | Expected: this lab only echoes. Real setup belongs in user-data |

## Cleanup

Terraform destroys only what it created, which here is the `terraform_data` resource. The key
pair, security group, and instance were made with the CLI, so you must remove them the same way.
The instance is billed per second until it terminates.

```bash
terraform destroy -auto-approve
rm -f terraform.tfvars
```

**Expected output**

```text
Destroy complete! Resources: 1 destroyed.
```

Now remove the three AWS objects, in this order — the security group cannot be deleted while the
instance still holds it.

```bash
aws ec2 terminate-instances --instance-ids i-0874d15af0a497f8f \
  --query 'TerminatingInstances[].[InstanceId,CurrentState.Name]' --output text
aws ec2 wait instance-terminated --instance-ids i-0874d15af0a497f8f
aws ec2 delete-security-group --group-id "$SG"
aws ec2 delete-key-pair --key-name lab-key
rm -f ~/.ssh/lab-key.pem
```

**Expected output** *(your instance id will differ)*

```text
i-0874d15af0a497f8f	shutting-down
```

`wait instance-terminated` prints nothing and returns after roughly 40 seconds; the two `delete`
commands print nothing on success. Confirm nothing is left running:

```bash
aws ec2 describe-instances \
  --filters 'Name=instance-state-name,Values=running,pending' \
  --query 'Reservations[].Instances[].InstanceId' --output text
```

Empty output means you are no longer being billed. If you skipped the `wait` and the security
group deletion failed with `DependencyViolation`, the instance was still shutting down — wait and
rerun that one command.

## Next steps

- Deep dive: [../docs/11-provisioners.md](../docs/11-provisioners.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab15-remote-exec-provisioner)
- Continue to [Lab 16 — Workspaces](lab16-workspaces.md)
