# Lab 17 — S3 backend

| | |
|---|---|
| **Goal** | Create a versioned S3 bucket, then move state out of the local directory into it, encrypted and lockable, using a backend config file. |
| **Time** | 40–50 minutes |
| **Tier** | Advanced |
| **Files** | `terraform/labs/lab17-s3-backend/` |

## Overview

A **backend** is where Terraform keeps its state file. Every lab so far used the default `local`
backend, which writes `terraform.tfstate` next to your code — fine alone, unworkable in a team:
the file lives on one laptop and two people applying at once overwrite each other.

The `s3` backend stores that same state file as an object in an Amazon S3 bucket — S3 is AWS's
object storage service, and a bucket is a durable, versioned folder in the cloud. Because state
now lives in one shared place, teammates and CI runners read the same truth, and Terraform can
take a **lock** so only one apply runs at a time.

This lab creates the bucket by hand, points the module at it, and confirms state landed there.
Terraform cannot create the bucket that holds its own state — the backend must already exist
before `init` can connect to it — so steps 5 to 9 build it with the AWS CLI. The same bucket
serves labs 17, 18, and 19, and lab 19 deletes it.

State locking uses `use_lockfile = true` — **native S3 locking**, where Terraform writes a small
`.tflock` object beside the state and a second apply refuses to start while it exists. No DynamoDB
table is needed. Older tutorials pair the S3 backend with a `dynamodb_table` argument; that
argument is deprecated, so do not add it. Native locking arrived in **Terraform 1.10** as an
experiment and is generally available from **1.11**, which is why this lab's `required_version` is
`>= 1.11.0` rather than the track's 1.5.0 floor. A learner on 1.5 to 1.9 would satisfy a 1.5.0
floor and then fail at `init` with `Unsupported argument: use_lockfile`, so the floor is raised
here to fail early with a clear message instead.

**A note on the expected output below.** Every block in this lab was captured from a real run in
`us-east-2`, including the bucket commands and the two `create-bucket` region errors. Values that
are unique to your account — bucket name, object sizes, timestamps, resource ids — are marked
*(yours will differ)*.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| S3 bucket, versioning enabled | Holds remote state for labs 17, 18, and 19 | Free to create; a few kilobytes of state costs well under a cent per month |
| S3 object at your `key` | The remote state file itself | Included above |
| `terraform_data.state_owner` | A trivial resource so state has something in it | Free |

## Before you start

- [ ] [Lab 16 — Workspaces](lab16-workspaces.md) completed
- [ ] Terraform 1.11.0 or newer, for generally-available `use_lockfile` (`terraform version`)
- [ ] AWS CLI version 2, and AWS credentials exported (see [Lab 00](lab00-aws-setup-and-init.md)) with `aws sts get-caller-identity` working
- [ ] Read [../docs/13-remote-state.md](../docs/13-remote-state.md)

No bucket is required in advance. You create it in this lab and reuse it in labs 18 and 19.

## Steps

### Step 1 — Read the empty backend block

```bash
cd terraform/labs/lab17-s3-backend
grep -A3 'backend' main.tf
```

**Expected output**

```text
  backend "s3" {}
}
```

The block is deliberately empty. Backend blocks cannot use variables, locals, or interpolation —
they are read before Terraform evaluates expressions, so `bucket = var.bucket` is impossible.
The supported way to keep account-specific values out of the code is a separate file, supplied at
`init` time. That is why this lab uses `backend.hcl` rather than `terraform.tfvars`.

### Step 2 — Initialize without connecting to the backend

`-backend=false` tells `init` to skip connecting to S3, so you can check your HCL before any AWS
call. Use this in CI pipelines that lint without deploy permissions.

```bash
terraform init -backend=false
```

**Expected output**

```text
Initializing provider plugins...
- terraform.io/builtin/terraform is built in to Terraform

Terraform has been successfully initialized!
```

### Step 3 — Validate the configuration with no credentials

```bash
terraform validate
```

**Expected output**

```text
Success! The configuration is valid.
```

This proves the syntax and types are correct without touching AWS at all.

### Step 4 — Confirm that a plan cannot run yet

```bash
terraform plan
```

**Expected output**

```text
Error: Backend initialization required, please run "terraform init"

Reason: Initial configuration of the requested backend "s3"
```

This error is expected and correct: Terraform will not plan until it knows where state lives.
Validation and planning have different requirements, which is exactly why CI can lint a module
it has no permission to deploy.

### Step 5 — Choose a globally unique bucket name

**S3 bucket names are globally unique across every AWS account in the world.** There is one
`tfstate` and one `terraform-state`, and someone else owns them. You must invent a name nobody has
taken, and you must use the *same* name in labs 17, 18, and 19.

`tfstate-yourname-4821` below is a **placeholder, not a usable name** — `create-bucket` with it
verbatim will fail, and if it somehow succeeds you are sharing a bucket with every other reader of
this manual. Replace `yourname` with your own name or initials and `4821` with four digits of your
own choosing. Names must be 3 to 63 characters, lowercase letters, digits, hyphens and dots only —
no uppercase, no underscores.

Holding it in a shell variable means the rest of labs 17 to 19 need no literal name at all.

```bash
export TF_STATE_BUCKET="tfstate-yourname-4821"
echo "$TF_STATE_BUCKET"
```

**Expected output** *(yours will differ — that is the point)*

```text
tfstate-yourname-4821
```

Environment variables live only in the terminal that set them. Re-export this line in every new
terminal you open across labs 17 to 19, and write the name down somewhere.

### Step 6 — Create the state bucket

```bash
aws s3api create-bucket --bucket "$TF_STATE_BUCKET" --region us-east-2 \
  --create-bucket-configuration LocationConstraint=us-east-2
```

**Expected output** *(yours will differ)*

```text
{
    "Location": "/tfstate-yourname-4821",
    "BucketArn": "arn:aws:s3:::tfstate-yourname-4821"
}
```

**Why the `--create-bucket-configuration` flag is there.** `CreateBucket` treats `us-east-1` as
its default location, so that one region — and only that one — must *omit* the flag. Every other
region, including the `us-east-2` this track uses, must pass it. Omitting it here fails with:

```text
An error occurred (IllegalLocationConstraintException) when calling the CreateBucket operation:
The unspecified location constraint is incompatible for the region specific endpoint this request
was sent to.
```

The rule is inverted in `us-east-1`, where passing the flag is what fails:

```text
An error occurred (InvalidLocationConstraint) when calling the CreateBucket operation: The
specified location-constraint is not valid
```

So the flag follows the region: name the region explicitly everywhere except `us-east-1`.

```bash
# us-east-2, ap-south-1, eu-central-1 ... : pass the flag
aws s3api create-bucket --bucket "$TF_STATE_BUCKET" --region ap-south-1 \
  --create-bucket-configuration LocationConstraint=ap-south-1

# us-east-1 only: omit it
aws s3api create-bucket --bucket "$TF_STATE_BUCKET" --region us-east-1
```

### Step 7 — Enable versioning on the bucket

Terraform overwrites the whole state object on every apply. **Versioning** keeps every prior copy,
so a truncated write, a bad migration, or an accidental `state rm` is recoverable — you fetch
yesterday's version. Without it, the overwritten copy is gone permanently. State history is the
reason this bucket exists, so this is not optional. New buckets have versioning off.

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

`put-bucket-versioning` prints nothing on success. The `get-` call is what confirms it.

### Step 8 — Confirm the bucket is not publicly readable

State files hold secrets in plaintext, so a public state bucket is a credential leak. Buckets
created since April 2023 block public access by default and encrypt objects with AES256 by
default, so there is nothing to change here — but verify rather than assume.

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

All four must be `true`. If any is `false`, or the call returns
`NoSuchPublicAccessBlockConfiguration`, set them explicitly:

```bash
aws s3api put-public-access-block --bucket "$TF_STATE_BUCKET" \
  --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

### Step 9 — Confirm the bucket is reachable and empty

No output means the bucket exists and you can list it. An error here is a bucket or permissions
problem, and it will not improve when Terraform tries.

```bash
aws s3 ls "s3://$TF_STATE_BUCKET"
```

**Expected output** *(an empty bucket prints nothing and exits 0)*

```text
```

### Step 10 — Create your backend config file

`backend.hcl` holds real account values, so it is not committed. `encrypt = true` asserts
server-side encryption for the state object, which routinely contains secrets.

```bash
cp backend.hcl.example backend.hcl
# Edit backend.hcl: replace the bucket value with your own $TF_STATE_BUCKET name
cat backend.hcl
```

**Expected output** *(yours will differ)*

```text
bucket       = "tfstate-yourname-4821"
key          = "labs/lab17/terraform.tfstate"
region       = "us-east-2"
encrypt      = true
use_lockfile = true
```

The shipped `backend.hcl.example` sets `bucket = "replace-with-your-globally-unique-state-bucket"`.
If `init` reports `NoSuchBucket` on that literal string, you skipped the edit.

### Step 11 — Initialize the real backend

```bash
terraform init -backend-config=backend.hcl
```

**Expected output** *(yours will differ)*

```text
Initializing the backend...

Successfully configured the backend "s3"! Terraform will automatically
use this backend unless the backend configuration changes.

Terraform has been successfully initialized!
```

If your credentials are missing, this is where it surfaces:

```text
Error: No valid credential sources found
```

### Step 12 — Apply, and watch the lock being taken and released

```bash
terraform apply -auto-approve
```

**Expected output** *(trimmed; ids will differ)*

```text
terraform_data.state_owner: Creating...
terraform_data.state_owner: Creation complete after 0s [id=c116e480-64e8-1830-cfa7-55dd50911820]
Releasing state lock. This may take a few moments...

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

state_owner = "shared-state"
```

`Releasing state lock` is the S3 lockfile being deleted, and it appears at the end of every remote
operation including `plan`. The matching `Acquiring state lock. This may take a few moments...`
line is only printed when the acquire is slow enough to be worth reporting, so on a fast, uncontended
bucket you usually see only the release. Lab 18 makes the acquire fail on purpose.

### Step 13 — Confirm there is no local state file

```bash
ls terraform.tfstate
```

**Expected output**

```text
ls: terraform.tfstate: No such file or directory
```

The missing local file is the proof that the move worked.

### Step 14 — Confirm the state object is in the bucket

```bash
aws s3 ls "s3://$TF_STATE_BUCKET/labs/lab17/"
```

**Expected output** *(timestamp and size will differ)*

```text
2026-08-29 14:47:19        940 terraform.tfstate
```

### Step 15 — Read state through the remote backend

The CLI reads the remote copy transparently — no flags, no local file.

```bash
terraform state list
terraform output state_owner
```

**Expected output** *(yours will differ)*

```text
terraform_data.state_owner
"shared-state"
```

## Done when

- [ ] `terraform init -backend=false` plus `validate` succeeded with no AWS credentials
- [ ] `terraform plan` refused with `Backend initialization required` before the real init
- [ ] `TF_STATE_BUCKET` holds a name you invented, not `tfstate-yourname-4821`
- [ ] `aws s3api get-bucket-versioning` reports `"Status": "Enabled"` on that bucket
- [ ] All four `PublicAccessBlockConfiguration` values are `true`
- [ ] `terraform init -backend-config=backend.hcl` reported the backend configured
- [ ] Apply printed `Releasing state lock` and `state_owner = "shared-state"`
- [ ] No `terraform.tfstate` exists locally, and the object exists in your bucket
- [ ] `terraform state list` works against the remote state
- [ ] You can explain why the backend block cannot reference `var.bucket`
- [ ] The bucket is still there — labs 18 and 19 need it

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `No valid credential sources found` | No AWS credentials in the environment | Export your keys as in Lab 00; backends do not read the provider block's `profile` |
| `AccessDenied` or `UnauthorizedOperation` | Your training account is permission-scoped | This is a policy boundary, not a broken config. Ask for `s3:GetObject`, `PutObject`, `DeleteObject`, `ListBucket` on that prefix |
| `NoSuchBucket` | Step 6 not run, `backend.hcl` still holds the example placeholder, or the name is mistyped | `aws s3 ls "s3://$TF_STATE_BUCKET"`, then check `bucket` in `backend.hcl` matches exactly |
| `BucketAlreadyExists` on `create-bucket` | Someone else in AWS owns that name | Pick a different name — you used the manual's placeholder or a common word. Re-export `TF_STATE_BUCKET` and retry |
| `BucketAlreadyOwnedByYou` on `create-bucket` | You already created it | Nothing to fix; continue at step 7 |
| `InvalidBucketName` | Uppercase letters or underscores in the name | Lowercase letters, digits, hyphens and dots only, 3–63 characters |
| `IllegalLocationConstraintException` | `--create-bucket-configuration` omitted. Every region except `us-east-1` requires it | Add `--create-bucket-configuration LocationConstraint=us-east-2` |
| `InvalidLocationConstraint` | Passed `LocationConstraint=us-east-1` — the one region that must omit it | Drop the flag when, and only when, the region is `us-east-1` |
| `TF_STATE_BUCKET` expands to nothing | New terminal; the export did not carry over | Re-run step 5 in this terminal |
| `Unsupported argument: use_lockfile` | Terraform older than 1.10 | Upgrade Terraform to 1.11 or newer |
| `Unsupported Terraform Core version` | Terraform older than the module's `>= 1.11.0` | Upgrade Terraform; do not lower `required_version` |
| `Error acquiring the state lock` | A previous run died mid-apply | Confirm nobody is applying, then `terraform force-unlock <LOCK_ID>` |
| `Backend configuration changed` | `backend.hcl` was edited after init | `terraform init -reconfigure`, or `-migrate-state` to move the state |
| `Variables not allowed` in the backend block | Someone added `bucket = var.bucket` | Backends cannot use variables; put the value in `backend.hcl` |

## Cleanup

Destroy this lab's resource now. **Do not delete the bucket yet.** Labs 18 and 19 store their
state in the same bucket, so deleting it here makes both fail at `terraform init` with
`NoSuchBucket`.

```bash
terraform destroy -auto-approve
rm -f backend.hcl
rm -rf .terraform
```

A few kilobytes in S3 costs effectively nothing, so leaving the bucket until the end of the
sequence is free. [Lab 19](lab19-state-migration.md#cleanup) deletes it, including the object
versions this lab's applies accumulated.

## Next steps

- Deep dive: [../docs/13-remote-state.md](../docs/13-remote-state.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab17-s3-backend)
- Continue to [Lab 18 — State keys and locking](lab18-state-keys-locking.md)
