# Lab 20 — Remote state consumer

| | |
|---|---|
| **Goal** | Read another module's outputs from its state file, and understand why those output names become a contract you cannot casually rename. |
| **Time** | 30–35 minutes |
| **Tier** | Advanced |
| **Files** | `terraform/labs/lab20-remote-state-consumer/` |

## Overview

Real infrastructure is not one giant module. It is split into stacks — network, database,
application — each with its own state, so a mistake in one cannot destroy another. But the
application stack still needs the network stack's VPC ID, so something must carry values across
that boundary.

The `terraform_remote_state` **data source** does that: it opens another module's state file and
exposes its outputs as read-only values. The module reading is the **consumer**; the module being
read is the **producer**. Nothing is created or modified — the consumer only looks.

The consequence is that a producer's `output` names stop being an implementation detail. They are
a published interface: rename `vpc_id` and every consumer's next plan breaks. This is the last
lab before the capstone, which is the first time you build a full stack whose outputs would be
worth consuming.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `data.terraform_remote_state.upstream` | Reads the lab 16 producer's state file | Free |
| Output `upstream_outputs` | The producer's entire output map | Free |
| Output `upstream_environment` | A single value reached into the map, the realistic pattern | Free |

## Before you start

- [ ] [Lab 19 — State migration](lab19-state-migration.md) completed
- [ ] [Lab 16 — Workspaces](lab16-workspaces.md) applied in **both** its `default` and `dev`
      workspaces, and **not** destroyed — this lab reads the two state files it left behind
      (`default` in step 2, `dev` in step 9). Lab 16's cleanup section is deliberately deferred
      until after this lab; if you already ran it, reapply lab 16 steps 5 to 8 before continuing.
- [ ] Read [../docs/13-remote-state.md](../docs/13-remote-state.md)

This lab creates no resources and needs no AWS credentials. The producer's state is a local file,
which keeps it runnable offline; the S3 producer variant is shown in step 9.

## Steps

### Step 1 — Move into the lab directory

```bash
cd terraform/labs/lab20-remote-state-consumer
ls
```

**Expected output**

```text
main.tf
terraform.tfvars.example
```

### Step 2 — Confirm the producer's state exists

If this file is missing, go back to lab 16 and apply it in the `default` workspace. The consumer
cannot invent the data it is meant to read.

```bash
ls ../lab16-workspaces/terraform.tfstate
```

**Expected output**

```text
../lab16-workspaces/terraform.tfstate
```

### Step 3 — Check which outputs the producer actually publishes

Read the contract before you consume it. These two names are everything this consumer can rely
on.

```bash
terraform -chdir=../lab16-workspaces output
```

**Expected output**

```text
labels = {
  "environment" = "default"
  "managed_by" = "terraform"
}
workspace = "default"
```

### Step 4 — Read the data source

`backend = "local"` and `config = { path = ... }` describe *where the producer's state lives*, not
where this module stores its own. A data source only reads.

```bash
grep -A5 'data "terraform_remote_state"' main.tf
```

**Expected output**

```text
data "terraform_remote_state" "upstream" {
  backend = "local"
  config = {
    path = var.upstream_state_path
  }
}
```

### Step 5 — Initialize and validate

```bash
terraform init
terraform validate
```

**Expected output**

```text
Initializing the backend...
Initializing provider plugins...
- terraform.io/builtin/terraform is built in to Terraform

Terraform has been successfully initialized!
Success! The configuration is valid.
```

### Step 6 — Plan, and notice the data source is read immediately

Data sources are read during the plan, not the apply — which is why the values are already known
here rather than showing `(known after apply)`.

```bash
terraform plan
```

**Expected output**

```text
data.terraform_remote_state.upstream: Reading...
data.terraform_remote_state.upstream: Read complete after 0s

Changes to Outputs:
  + upstream_environment = "default"
  + upstream_outputs     = {
      + labels    = {
          + environment = "default"
          + managed_by  = "terraform"
        }
      + workspace = "default"
    }

You can apply this plan to save these new output values to the Terraform
state, without changing any real infrastructure.
```

### Step 7 — Apply and read the values

```bash
terraform apply -auto-approve
```

**Expected output**

```text
data.terraform_remote_state.upstream: Reading...
data.terraform_remote_state.upstream: Read complete after 0s

Apply complete! Resources: 0 added, 0 changed, 0 destroyed.

Outputs:

upstream_environment = "default"
upstream_outputs = {
  "labels" = {
    "environment" = "default"
    "managed_by" = "terraform"
  }
  "workspace" = "default"
}
```

`0 added` confirms the consumer touched nothing. `upstream_environment` reached two levels into
the producer's `labels` map — indexing like that is the contract at its most brittle.

### Step 8 — Confirm the consumer's own state holds only the data source

```bash
terraform state list
```

**Expected output**

```text
data.terraform_remote_state.upstream
```

No managed resources at all — the consumer's state records only what it read.

### Step 9 — Point at a different producer state

A named workspace's state lives under `terraform.tfstate.d/<name>/`, as in lab 16. Switching
producers is a variable change, not a code change.

```bash
terraform apply -auto-approve \
  -var='upstream_state_path=../lab16-workspaces/terraform.tfstate.d/dev/terraform.tfstate'
```

**Expected output**

```text
Apply complete! Resources: 0 added, 0 changed, 0 destroyed.

Outputs:

upstream_environment = "dev"
upstream_outputs = {
  "labels" = {
    "environment" = "dev"
    "managed_by" = "terraform"
  }
  "workspace" = "dev"
}
```

For a producer using the S3 backend from labs 17 and 18, the same data source changes only its
backend and config — the rest of the module is untouched:

```hcl
data "terraform_remote_state" "upstream" {
  backend = "s3"
  config = {
    bucket = "tfstate-yourname-4821"
    key    = "labs/dev/network/terraform.tfstate"
    region = "us-east-2"
  }
}
```

### Step 10 — Break the contract on purpose

Ask for an output the producer does not publish — exactly what a rename looks like downstream.

```bash
terraform console
> data.terraform_remote_state.upstream.outputs.vpc_id
```

**Expected output**

```text
Error: Unsupported attribute

This object does not have an attribute named "vpc_id".
```

Type `exit` to leave the console. The failure lands in the *consumer* while the change was made
in the producer — which is why output names need the same care as a public API.

## Done when

- [ ] `terraform -chdir=../lab16-workspaces output` showed the two producer outputs
- [ ] `terraform plan` read the data source and resolved both output values
- [ ] Apply reported `0 added, 0 changed, 0 destroyed`
- [ ] `terraform state list` returned only the data source address
- [ ] Pointing at the `dev` workspace state changed `upstream_environment` to `"dev"`
- [ ] Requesting a nonexistent output produced `Unsupported attribute`
- [ ] You can explain why exporting whole resource objects is worse than exporting `vpc_id`

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `Error: Failed to read state file` / no such file | Lab 16 was destroyed or never applied | Apply lab 16 in its `default` workspace, then retry |
| `upstream_outputs = {}` | Producer state exists but has no outputs recorded | Reapply the producer; outputs are only stored on apply |
| `Unsupported attribute` on `outputs.labels` | Pointing at a producer that publishes different outputs | Check the path, then rerun step 3 against that directory |
| Reads the wrong environment | Pointing at `terraform.tfstate` instead of the workspace file | Named workspaces live under `terraform.tfstate.d/<name>/` |
| Consumer plan changes after a producer apply | The producer's output values moved | Expected: the consumer re-reads on every plan |
| `AccessDenied` with the S3 variant | No read permission on the producer's key | A policy boundary, not a config error — request `s3:GetObject` on that prefix |
| `Backend configuration changed` with the S3 variant | Switched `backend` inside the data source after init | Rerun `terraform init` |

## Cleanup

```bash
terraform destroy -auto-approve
```

Destroying the consumer does not affect the producer. Lab 16 is now safe to clean up — return to
its [cleanup section](lab16-workspaces.md#cleanup) and run the commands you deferred.

## Next steps

- Deep dive: [../docs/17-project-structure.md](../docs/17-project-structure.md)
- Visual: [../html/advanced.html](../html/advanced.html)
- Continue to [Lab 21 — Dynamic Blocks](lab21-dynamic-blocks.md)
