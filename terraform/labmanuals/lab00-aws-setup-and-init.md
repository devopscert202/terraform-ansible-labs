# Lab 00 — AWS Setup and First Init

| | |
|---|---|
| **Goal** | Prove your AWS credentials work, write your first provider block, and finish with a successful `terraform init`. |
| **Time** | 25–35 minutes |
| **Tier** | Basic |
| **Files** | `../labs/lab00-aws-setup-and-init/` |

## Overview

Terraform is a tool that creates cloud infrastructure from text files. Instead of clicking
buttons in a web page, you describe what you want in a file and Terraform makes it real. Before
it can do that, it needs permission to talk to your AWS account, and that permission comes from
a pair of strings called **access keys**.

This lab sets those keys up, proves they work, checks the one account-level prerequisite the later
labs depend on, and runs `terraform init` — the command that prepares a folder for Terraform.
Nothing here costs money.

There are two ways to give Terraform your keys. Environment variables are the primary method
and are covered in Steps 3 to 5. A named profile is the alternate, covered in Steps 6 to 8; it
saves the keys to a file so you do not retype them every session. Do one or the other, not both.

**Every credential value printed in this manual is a fake placeholder.** Key values appear as
`AKIA_REPLACE_WITH_YOUR_ACCESS_KEY_ID` and similar, account numbers as `123456789012`. None of
them work, and none of them are meant to be pasted. Your real values come from your own AWS
account — the IAM console under **Security credentials → Access keys**, or a training portal that
issues you a temporary key pair. If your instructor handed you a key, that is your value.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| Shell environment variables | Hold your AWS credentials for this terminal session only | None |
| `~/.aws/credentials` entry | Alternate path only: the same keys saved under a profile name | None |
| `provider "aws"` block | Tells Terraform which cloud and which region to use | None |
| `data "aws_caller_identity"` | Reads back who you are; reads only, creates nothing | None |
| Default VPC and its default subnets | Only if your account has none: the network labs 03, 06, and 12 place resources in | None — a VPC, subnet, and internet gateway are free |
| `.terraform/` directory | Where `init` stores the downloaded AWS plugin | None |

## Before you start

- [ ] An AWS account you are allowed to experiment in — training or sandbox, never production
- [ ] An access key ID and secret access key **issued to you** for that account, from the IAM console or your training portal. The manual cannot supply these; no value printed here is real
- [ ] Terraform 1.5.0 or newer, and AWS CLI version 2, installed
- [ ] A terminal open at the root of this repository

## Steps

### Step 1 — Confirm Terraform is installed

```bash
terraform version
```

**Expected output**

```text
Terraform v1.14.8
on darwin_arm64
```

Any version numbered 1.5.0 or higher is fine. `command not found` means Terraform is not
installed yet.

### Step 2 — Confirm the AWS CLI is installed

The AWS CLI is a separate program from Terraform. You use it here to test your keys before
Terraform ever touches them.

```bash
aws --version
```

**Expected output**

```text
aws-cli/2.34.45 Python/3.14.6 Darwin/25.6.0 source/arm64
```

### Step 3 — Clear settings left over from earlier work

`AWS_PROFILE` is a variable that points at a saved set of credentials. If one is already set,
AWS silently uses it and ignores the keys you are about to type — a confusing failure, because
nothing reports an error.

```bash
unset AWS_PROFILE AWS_SESSION_TOKEN
```

`unset` removes the variable entirely, which is the only correct fix. Do not instead set it to an
empty string (`export AWS_PROFILE=""`): the empty value counts as a real profile name, and every
later AWS command fails, exiting 255, with

```text
aws: [ERROR]: The config profile () could not be found
```

The empty parentheses are the profile name AWS is looking for. `unset AWS_PROFILE` clears it;
`export AWS_PROFILE=""` does not.

### Step 4 — Load your access keys into this terminal

An access key comes in two parts. The **access key ID** starts with `AKIA`, is 20 characters long,
and is the public half, like a username. The **secret access key** is a 40-character random string
and is the private half, like a password. Anyone holding both can act as you in AWS, so never paste
either value into a `.tf` file and never commit them to git, where they are permanent and widely
readable. Environment variables live only in the terminal window you type them into and vanish when
you close it, which is why this is the method used here.

Substitute your own two values into the block below. The words in capitals are placeholders and
will not authenticate — a real key ID looks like `AKIA` followed by 16 more uppercase characters,
and the secret is 40 mixed-case characters that may include `/` and `+`. Both come from your own
account: IAM console → **Security credentials → Access keys → Create access key**, or whatever your
training portal issued you. AWS shows the secret exactly once, at creation.

```bash
export AWS_ACCESS_KEY_ID="AKIA_REPLACE_WITH_YOUR_ACCESS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="REPLACE_WITH_YOUR_SECRET_ACCESS_KEY"
export AWS_DEFAULT_REGION="us-east-1"
```

`us-east-1` is the only value in that block you should keep verbatim. A **region** is the physical
group of data centres your resources live in; every lab in this track uses `us-east-1`.

Quote the secret in single quotes instead of double if it contains a `$` or a backtick, otherwise
your shell will try to expand it and you will export a truncated key. Prefixing the `export` lines
with a single space keeps them out of your shell history in `bash` and `zsh` when `HISTCONTROL` or
`HIST_IGNORE_SPACE` is set.

### Step 5 — Prove the credentials work

Do not assume the exports worked. Nothing in step 4 contacts AWS, so a mistyped key, an
unquoted secret, or a leftover `AWS_PROFILE` produces no error until something calls the API.
This step is that call, and it is the only evidence that your credentials are correct. It asks AWS
a single question: who am I?

```bash
aws sts get-caller-identity
```

**Expected output** *(your `UserId`, `Account`, and `Arn` will differ — these are placeholders)*

```text
{
    "UserId": "AIDA2EXAMPLEID4NEXAMPLE",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/odl_user_1234567"
}
```

Three things make this a pass, and all three must hold:

1. The command exits without an error block.
2. `Account` is a real 12-digit number, not `123456789012`, and it is the training account you
   were given.
3. `Arn` names the identity you expect — not a role or user belonging to some other account.

If the output shows an account you do not recognise, a leftover `AWS_PROFILE` or an
`~/.aws/credentials` entry is winning over your exports. Rerun step 3, then step 4. If the command
fails outright, fix your keys before going on — Terraform authenticates the same way and will fail
the same way, with a less obvious message.

**If this step passed, skip to Step 9.** Steps 6 to 8 are the alternate credential path.

### Step 6 — Alternate: save your keys as a named profile

A **profile** is a named set of credentials saved to a file on disk, so you do not retype them
each session. This is the better choice once you work with several accounts at once.

```bash
aws configure --profile tf-labs
```

The command asks four questions. Enter your own two key values — the same ones from step 4 — then
the region and output format.

**Expected prompts** *(the two key values shown are placeholders; enter yours)*

```text
AWS Access Key ID [None]: AKIA_REPLACE_WITH_YOUR_ACCESS_KEY_ID
AWS Secret Access Key [None]: REPLACE_WITH_YOUR_SECRET_ACCESS_KEY
Default region name [None]: us-east-1
Default output format [None]: json
```

The values are written to `~/.aws/credentials` and `~/.aws/config` under the heading `tf-labs`.
That file is still a plain-text secret on your machine and must never be committed.

### Step 7 — Alternate: verify the profile

Naming the profile explicitly proves the saved credentials work on their own, independently of
any environment variable.

```bash
aws sts get-caller-identity --profile tf-labs
```

**Expected output** *(placeholder values again — check yours against the three conditions in
step 5)*

```text
{
    "UserId": "AIDA2EXAMPLEID4NEXAMPLE",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/odl_user_1234567"
}
```

### Step 8 — Alternate: point Terraform at the profile

Terraform does not read `--profile` from the command line. Name the profile inside the provider
block instead. Open `../labs/lab00-aws-setup-and-init/main.tf` and add the `profile` line:

```hcl
provider "aws" {
  region  = "us-east-1"
  profile = "tf-labs"
}
```

Remove that line again if you later switch back to environment variables, otherwise Terraform
keeps using the saved profile and ignores them.

### Step 9 — Confirm the account has a default VPC

A **VPC** is a private network inside AWS, and every region normally ships with one **default VPC**
that AWS pre-built for you. Labs 03, 06, and 12 declare an EC2 instance without naming a subnet and
a security group without naming a VPC, so AWS puts them in that default VPC. Those labs stay
minimal on purpose — building a network from scratch is [Lab 21](lab21-capstone-vpc-ec2.md), and
the concepts are covered in [the AWS primer](../html/aws-primer.html).

The default VPC is not guaranteed. It can be deleted, and some account-vending processes never
create one. This is worth one command now because `terraform plan` does **not** detect a missing
default VPC — the failure appears only at `terraform apply`, in lab 03, as
`VPCIdNotSpecified: No default VPC for this user`. That is the first AWS resource you ever create,
and the message points at nothing you did.

```bash
aws ec2 describe-vpcs --filters Name=isDefault,Values=true \
  --query 'Vpcs[].[VpcId,CidrBlock]' --output text
```

**Expected output** *(your VPC id will differ; the CIDR is usually `172.31.0.0/16`)*

```text
vpc-0fa2e04ddfd87b3a9	172.31.0.0/16
```

**Empty output is the failure condition, not a pass.** This is the trap: a `describe` call that
finds nothing prints nothing and still exits 0, which reads like "checked, no problems". One line
of output means you have a default VPC. No output at all means you have none, and labs 03, 06, and
12 will fail at apply.

If the output was empty, create one:

```bash
aws ec2 create-default-vpc \
  --query 'Vpc.[VpcId,CidrBlock,State,IsDefault]' --output text
```

**Expected output** *(ids will differ)*

```text
vpc-0fa2e04ddfd87b3a9	172.31.0.0/16	pending	True
```

`pending` becomes `available` within seconds. Then rerun the `describe-vpcs` command above and
confirm it now prints a line.

Running `create-default-vpc` when one already exists creates nothing and changes nothing. It
refuses, exiting 254:

```text
aws: [ERROR]: An error occurred (DefaultVpcAlreadyExists) when calling the CreateDefaultVpc
operation: A Default VPC already exists for this account in this region.
```

So the command is safe to run when you are unsure — there is no way to end up with two.

### Step 10 — Confirm the default VPC has default subnets

An instance launches into a **subnet**, not into a VPC, so a default VPC with no default subnets
fails the same way. `create-default-vpc` creates one default subnet per availability zone
automatically, so this normally needs no action — but a subnet that was deleted afterwards is not
recreated for you, so verify rather than assume.

```bash
aws ec2 describe-subnets --filters Name=default-for-az,Values=true \
  --query 'Subnets[].[SubnetId,AvailabilityZone]' --output text
```

**Expected output** *(ids will differ; `us-east-1` currently has six zones, and the order varies)*

```text
subnet-00207cf1bd3d27e28	us-east-1b
subnet-05b29dd82ba0724d4	us-east-1f
subnet-0646196e0fc96b9d1	us-east-1d
subnet-0938ef78433ccd094	us-east-1a
subnet-045819c0d9fb81992	us-east-1e
subnet-08aec30f157caf726	us-east-1c
```

One line per zone. Empty output is again the failure, and one missing zone is fine — the labs do
not pin a zone. If a zone you need is absent, recreate its subnet with
`aws ec2 create-default-subnet --availability-zone us-east-1a`, which refuses with
`DefaultSubnetAlreadyExistsInAvailabilityZone` if one is already there.

### Step 11 — Read the lab configuration

```bash
cd terraform/labs/lab00-aws-setup-and-init
cat main.tf
```

Three pieces matter. The `terraform` block states the minimum version and which **provider** —
the plugin that knows how to talk to a given cloud — is needed. The `provider "aws"` block sets
the region and contains no keys. The `data` block reads your identity without creating anything.

### Step 12 — Initialize the directory

`terraform init` downloads the AWS provider plugin into this folder. Run it once per lab
directory, before any other Terraform command.

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
selections it made above. Include this file in your version control repository
so that Terraform can guarantee to make the same selections by default when
you run "terraform init" in the future.

Terraform has been successfully initialized!
```

`.terraform.lock.hcl` records the exact plugin version so every teammate gets the same one.

### Step 13 — Confirm Terraform can reach AWS

```bash
terraform plan
```

**Expected output** *(the id is your account number; `123456789012` is a placeholder)*

```text
data.aws_caller_identity.current: Reading...
data.aws_caller_identity.current: Read complete after 1s [id=123456789012]

No changes. Your infrastructure matches the configuration.
```

`No changes` is the goal: Terraform authenticated to AWS and found nothing to create. The `id`
should match the `Account` value from step 5 — if it does not, Terraform and the AWS CLI are
reading different credentials.

## Done when

- [ ] `terraform version` reports 1.5.0 or newer
- [ ] `aws sts get-caller-identity` returned your own 12-digit training account number, not `123456789012`
- [ ] No placeholder string beginning `AKIA_REPLACE` or `REPLACE_WITH` remains in your exports
- [ ] `describe-vpcs --filters Name=isDefault,Values=true` printed a VPC id — one line, not empty
- [ ] `describe-subnets --filters Name=default-for-az,Values=true` printed at least one subnet
- [ ] `terraform init` printed `Terraform has been successfully initialized!`
- [ ] `terraform plan` printed `No changes`, with an `id` matching your account number
- [ ] No access key appears in any `.tf` file, and none is staged for commit

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `The config profile () could not be found` | `AWS_PROFILE` set to an empty string | `unset AWS_PROFILE` |
| Identity shows an unexpected account | A leftover `AWS_PROFILE` is overriding your keys | `unset AWS_PROFILE AWS_SESSION_TOKEN`, then re-export |
| `InvalidClientTokenId` | Access key ID mistyped, deactivated, or still the manual's placeholder | Re-copy your own 20-character key ID; confirm it is active in IAM |
| `SignatureDoesNotMatch` | Secret key mistyped, truncated, or partly eaten by the shell | Re-copy the full 40-character secret; wrap it in single quotes if it contains `$` or a backtick |
| `ExpiredToken` | Temporary sandbox credentials timed out | Issue fresh keys and export them again |
| `No valid credential sources found` | Not exported in this terminal | Re-run the exports in the window you are using |
| `The config profile (tf-labs) could not be found` | Step 6 not run, or the name is misspelled | Re-run `aws configure --profile tf-labs` |
| `describe-vpcs` prints nothing | The account has no default VPC | Not a pass. Run `aws ec2 create-default-vpc`, then rerun the describe |
| `VPCIdNotSpecified: No default VPC for this user` at `terraform apply` in lab 03, 06, or 12 | Step 9 skipped, or the default VPC was deleted since | `aws ec2 create-default-vpc`, then rerun `terraform apply`. `terraform plan` cannot detect this, so it never warned you |
| `DefaultVpcAlreadyExists` | You already have one | Nothing to fix; the check in step 9 has passed |
| `UnauthorizedOperation` on `create-default-vpc` | The training policy withholds `ec2:CreateDefaultVpc` | A policy boundary, not a config error. Ask for a default VPC to be created in the account |
| `UnauthorizedOperation` on a later lab | Training accounts are permission-scoped | Not a broken credential — the action is outside your account's policy |

## Cleanup

This lab creates no billable infrastructure, so there is nothing to destroy. Leave the default VPC
in place — it costs nothing and labs 03, 06, and 12 depend on it. When you finish the track,
delete the access keys in the AWS IAM console — rotating keys you no longer need limits the
damage if they ever leak.

```bash
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_DEFAULT_REGION
```

If you used the alternate path, list your saved profiles, then delete the `[tf-labs]` section
from `~/.aws/credentials` and `~/.aws/config` in an editor. Remove the `profile` line from the
provider block as well.

```bash
aws configure list-profiles
```

## Next steps

- Deep dive: [Getting started](../docs/basic/01-getting-started.md)
- Visual: [Basic tier concepts](../html/basic.html)
- Continue to [Lab 01 — Providers and Init](lab01-providers-init.md)
