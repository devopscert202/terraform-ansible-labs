# Remote State, Backends, Locking, and Workspaces

Deep dive for lab16 through lab20. Covers why a team cannot use local state, how the S3 backend is
configured, how state locking actually works now that DynamoDB is deprecated, how to lay out state
keys, what workspaces do and do not isolate, and how one configuration reads another's outputs.

## Why local state stops working

Local state (covered in [`../intermediate/07-state.md`](../intermediate/07-state.md)) is a file in
your working directory. It works perfectly for one person. Add a second person and every one of its
properties becomes a problem:

| Problem | Consequence |
|---|---|
| The file is on your laptop | Nobody else can plan or apply. CI certainly cannot |
| Two people can apply at once | Both read the same state, both write it, the second overwrites the first. Resources are silently orphaned |
| No history | A bad apply is unrecoverable beyond the single `.backup` generation |
| No encryption at rest | And the file contains secrets in plain text |
| Emailing it around | Now the secrets are in an inbox too |

A **backend** is Terraform's answer: configuration telling it to store state somewhere other than
the local disk. The S3 backend addresses all five — shared location, locking, versioning,
encryption, and access control.

**Visual summary:** [`../../html/advanced.html`](../../html/advanced.html)

## The S3 backend (lab17)

Lab17's configuration is deliberately almost empty:

```hcl
terraform {
  required_version = ">= 1.5.0"
  backend "s3" {}
}

resource "terraform_data" "state_owner" { input = "shared-state" }
output "state_owner" { value = terraform_data.state_owner.output }
```

The empty `backend "s3" {}` block is a **partial configuration**. The settings arrive at `init`
time from a separate file, because of a hard constraint on backend blocks:

> A `backend` block cannot use variables, locals, or any expression. Only literal values.

That is not an oversight. The backend must be resolved before Terraform can read state, and
variables cannot be evaluated before state is available. So `var.bucket` in a backend block is
impossible, and the workaround is a `-backend-config` file:

`backend.hcl.example`:

```hcl
bucket       = "replace-with-your-globally-unique-state-bucket"
key          = "labs/lab17/terraform.tfstate"
region       = "us-east-1"
encrypt      = true
use_lockfile = true
```

```bash
cp backend.hcl.example backend.hcl   # then edit in your real bucket name
terraform init -backend-config=backend.hcl
```

| Setting | Meaning |
|---|---|
| `bucket` | The S3 bucket holding state. Bucket names are globally unique across all of AWS, so yours must be your own |
| `key` | The object path inside the bucket. This is what separates one configuration's state from another's |
| `region` | The bucket's region |
| `encrypt = true` | Server-side encryption on the state object. Given state holds secrets in plain text, treat this as mandatory |
| `use_lockfile = true` | Native S3 state locking — see below |

Keep `backend.hcl` out of version control (commit only the `.example`) since it names a real
bucket, and enable **S3 bucket versioning** on that bucket. Versioning is your only real undo: if
an apply corrupts state, you restore the previous object version. Set it up before you need it.

## State locking

A **lock** stops two applies running against the same state at once. Without one, two engineers
who apply simultaneously both read the same starting state and the last writer wins — the other's
resources still exist in AWS but are no longer in state, invisible and unmanaged.

Terraform acquires the lock at the start of any state-writing operation and releases it at the end.
A second run finds the lock and refuses to start rather than corrupting anything.

### Native S3 locking (current approach)

```hcl
bucket       = "myorg-terraform-state"
key          = "labs/dev/network/terraform.tfstate"
region       = "us-east-1"
encrypt      = true
use_lockfile = true
```

`use_lockfile = true` is all it takes. Terraform writes a small object alongside your state at the
same path with a `.tflock` suffix — for the key above, `labs/dev/network/terraform.tfstate.tflock`
— using S3 conditional writes so that only one writer can create it. One bucket does both jobs.

**Version requirement:** native S3 locking arrived as an experimental option in Terraform **1.10**
and became generally available in **1.11**. It is what every lab in this track uses. If you are
running an older CLI, `use_lockfile` will not work and you need the legacy mechanism below — this
is a good reason to check `terraform version` before starting lab17.

### DynamoDB locking (deprecated)

For years, locking the S3 backend required a separate DynamoDB table:

```hcl
# Deprecated. Shown so you recognise it in existing code.
dynamodb_table = "terraform-locks"
```

The table needed a partition key named `LockID` of type `String`, plus its own IAM policy, its own
cost line, and its own Terraform code to create it. You will meet this pattern constantly in
tutorials and existing repositories, because it was the only option before Terraform 1.10.

As of Terraform 1.11 the `dynamodb_table` argument is **deprecated** and is slated for removal in a
future minor version. Do not write new configurations against it.

Migrating is safe and needs no downtime, because the two arguments are allowed to coexist:

1. Add `use_lockfile = true` while keeping `dynamodb_table`. Terraform now acquires a lock from
   both systems on every run, so old and new CLI versions can operate against the same state.
2. Once everyone and every CI job is on Terraform 1.11 or newer, remove `dynamodb_table` and
   re-run `init`.
3. Delete the DynamoDB table.

### When a lock is stuck

If Terraform is killed mid-apply the lock can survive:

```text
Error: Error acquiring the state lock

Lock Info:
  ID:        d7b8e3f1-...
  Operation: OperationTypeApply
  Who:       you@laptop
  Created:   2026-08-29 10:14:02 UTC
```

Read the lock info first. If the named person is genuinely still applying, wait — that is the lock
doing its job. Only if you have confirmed nothing is running:

```bash
terraform force-unlock <LOCK_ID>
```

`force-unlock` releases the lock without checking whether an apply is in progress. Running it while
someone is actually applying is how you get the corruption the lock existed to prevent. Confirm
with the person named in the lock info first, every time.

## State keys (lab18)

The `key` is the object path in the bucket, and it is what keeps environments apart. Two
configurations sharing a key share state, with predictably bad results.

Lab18 builds the convention from variables so the structure is explicit:

```hcl
variable "environment" {
  type        = string
  default     = "dev"
  description = "Environment segment of the state key, e.g. dev or staging."
}

variable "component" {
  type        = string
  default     = "network"
  description = "Component segment of the state key, e.g. network or app."
}

locals {
  recommended_key = "labs/${var.environment}/${var.component}/terraform.tfstate"
}
```

That produces `labs/dev/network/terraform.tfstate`. The pattern generalises to
`<org-or-repo>/<environment>/<component>/terraform.tfstate`:

| Key | Holds |
|---|---|
| `labs/dev/network/terraform.tfstate` | Dev VPC, subnets, gateways |
| `labs/dev/app/terraform.tfstate` | Dev instances and load balancers |
| `labs/prod/network/terraform.tfstate` | Production networking |
| `labs/prod/app/terraform.tfstate` | Production compute |

Remember that `locals` cannot feed the backend block — lab18 computes the key to *demonstrate* the
convention, while the real value is supplied literally in `backend.hcl`.

Splitting by **component** as well as environment is the part people skip, and it is where the
value is. Each key is a separate lock, a separate apply, and a separate blast radius. A mistake in
`dev/app` cannot touch `prod/network`. Small, frequently-changing components get their own state so
that applying them does not require planning the whole world.

## Workspaces (lab16)

A **workspace** is multiple state files under one backend configuration. Terraform starts you in a
workspace called `default`.

```hcl
locals {
  environment = terraform.workspace
  labels      = { environment = terraform.workspace, managed_by = "terraform" }
}

output "workspace" { value = terraform.workspace }
```

`terraform.workspace` is a built-in giving the current workspace's name, which lets one
configuration name its resources per environment.

```bash
terraform workspace list           # * marks the current one
terraform workspace new dev
terraform workspace select dev
terraform workspace show
```

With the S3 backend, non-default workspaces get a prefixed key — by default under
`env:/<workspace>/<key>`, adjustable with `workspace_key_prefix`. With local state they land in
`terraform.tfstate.d/<name>/`.

### Workspaces versus separate keys

| | Workspaces | Separate state keys |
|---|---|---|
| Configuration | One directory, one backend block | One directory per stack, or one backend file per environment |
| Switching | `terraform workspace select` | `terraform init -backend-config=<file>` |
| Credentials | **Shared. One set for all workspaces** | Separate per environment |
| Divergence between environments | Not possible — same code | Possible, and reviewable |
| Risk of applying to the wrong one | **High. Current workspace is invisible in your shell** | Low — you chose a directory |

Workspaces are excellent for ephemeral, identical environments: a per-branch sandbox, a
short-lived test stack, a feature preview.

They are a poor fit for dev/staging/prod, for two reasons that are worth being blunt about. First,
all workspaces share one backend configuration and therefore one set of credentials — so nothing
technically prevents an apply in the `prod` workspace using dev credentials, or vice versa. Second,
the current workspace is invisible: nothing in your prompt tells you that you are in `prod`, and
`terraform apply` will not remind you. The standard failure is applying a dev change to production
because you forgot to switch back.

For real environment boundaries, use separate state keys with separate credentials and separate
directories. Make the boundary something you have to walk through, not something you have to
remember.

## State migration (lab19)

Adding a backend to a configuration that already has local state means moving the state. Terraform
handles it, but only if you ask.

Lab19 starts with the backend commented out:

```hcl
terraform {
  required_version = ">= 1.5.0"

  # Step 5 of the lab manual has you add the S3 backend block here:
  #   backend "s3" {}
}
```

The sequence:

```bash
terraform apply                                    # create resources with local state
cp terraform.tfstate terraform.tfstate.premigration # back it up. do not skip this
# add backend "s3" {} to main.tf
terraform init -backend-config=backend.hcl -migrate-state
```

Terraform detects the backend change and offers to copy existing state to the new location. With
`-migrate-state` you are confirming that is what you want.

```text
Do you want to copy existing state to the new backend?
  Enter "yes" to copy and "no" to start with an empty state.
```

Answer carefully. **`no` means Terraform starts with empty state** — it forgets every resource it
manages, and the next `plan` proposes creating everything again while the originals become
orphans. This prompt is the single riskiest moment in the whole track.

Afterwards, verify before cleaning up:

```bash
terraform state list      # same addresses as before?
terraform plan            # "No changes" confirms nothing was lost
rm terraform.tfstate      # only now, and keep the backup a while
```

The related flag is `-reconfigure`, which changes backends **without** copying state. It is for
pointing a configuration at a different, already-populated state, and using it by mistake in place
of `-migrate-state` produces the empty-state outcome above.

## Remote state consumers (lab20)

Splitting infrastructure across several state files raises an obvious question: how does the
application stack learn the VPC ID that the network stack created?

The `terraform_remote_state` data source reads another configuration's **outputs**:

```hcl
variable "upstream_state_path" {
  type        = string
  description = "Path to the producer lab's state file that this consumer reads."
  default     = "../lab16-workspaces/terraform.tfstate"
}

data "terraform_remote_state" "upstream" {
  backend = "local"
  config = {
    path = var.upstream_state_path
  }
}

output "upstream_outputs" {
  value = data.terraform_remote_state.upstream.outputs
}

output "upstream_environment" {
  value = data.terraform_remote_state.upstream.outputs.labels.environment
}
```

Lab20 reads lab16's local state file, which keeps the lab free and credential-free. Against a real
S3 backend the shape is the same, with the producer's backend settings in `config`:

```hcl
data "terraform_remote_state" "network" {
  backend = "s3"
  config = {
    bucket = "myorg-terraform-state"
    key    = "labs/dev/network/terraform.tfstate"
    region = "us-east-1"
  }
}

resource "aws_instance" "app" {
  subnet_id = data.terraform_remote_state.network.outputs.subnet_id
  # ...
}
```

Two constraints define how this should be used.

**Only outputs are readable.** `data.terraform_remote_state.network.outputs.subnet_id` works;
reaching into the producer's resources does not. So the producer's output list is a deliberate
published contract, and removing or renaming an output breaks every consumer.

**Reading state requires read access to the entire state file** — including every secret in it, for
every resource the producer manages. That is a wide grant for the sake of one subnet ID. Where the
values are in AWS anyway, prefer a data source (`aws_vpc` with tag filters) or SSM Parameter Store,
both of which let you grant access to just the value in question.

## State still contains secrets

A remote backend changes where state lives, not what it holds. Every password, key, and certificate
is still in there in plain text. Remote state makes this more consequential, not less, because the
file is now shared:

- Set `encrypt = true`. Always.
- Enable bucket versioning, and note that old versions contain old secrets — set a lifecycle policy.
- Scope the bucket policy tightly. **Read access to the state bucket is effectively read access to
  your production credentials.**
- Block public access at the bucket and account level.
- Never grant broad `s3:GetObject` on the state prefix for convenience.

## Command reference

```bash
cd terraform/labs/lab17-s3-backend
cp backend.hcl.example backend.hcl        # edit in your own bucket name
terraform init -backend-config=backend.hcl
terraform apply

cd ../lab18-state-keys-locking
terraform init -backend-config=backend.hcl
terraform apply -var="environment=dev" -var="component=network"
terraform output recommended_state_key
# start a second apply in another terminal to watch the lock refuse it

cd ../lab16-workspaces
terraform init
terraform workspace list
terraform workspace new dev
terraform apply
terraform workspace select default

cd ../lab19-state-migration
terraform init && terraform apply         # local state first
# add backend "s3" {} to main.tf, then:
terraform init -backend-config=backend.hcl -migrate-state
terraform state list                      # verify nothing was lost

cd ../lab20-remote-state-consumer
terraform init
terraform apply                           # reads lab16's state
terraform output upstream_environment

# useful anywhere
terraform state pull > backup.tfstate      # download remote state
terraform force-unlock <LOCK_ID>           # emergency only, after confirming
```

## Where next

- Assembling all of this into a repository layout: [`projects.md`](projects.md)
- The capstone that builds a real network end to end:
  [`../../labmanuals/lab21-capstone-vpc-ec2.md`](../../labmanuals/lab21-capstone-vpc-ec2.md)

## Hands-On Labs

| Lab | Description |
|---|---|
| [Lab 16: Workspaces](../../labmanuals/lab16-workspaces.md) | `terraform workspace`, `terraform.workspace`, per-workspace state |
| [Lab 17: S3 Backend](../../labmanuals/lab17-s3-backend.md) | Partial backend configuration supplied via `backend.hcl` |
| [Lab 18: State Keys and Locking](../../labmanuals/lab18-state-keys-locking.md) | Key conventions per environment and component, and native S3 locking |
| [Lab 19: State Migration](../../labmanuals/lab19-state-migration.md) | Move local state to S3 with `init -migrate-state` |
| [Lab 20: Remote State Consumer](../../labmanuals/lab20-remote-state-consumer.md) | Read another configuration's outputs with `terraform_remote_state` |
