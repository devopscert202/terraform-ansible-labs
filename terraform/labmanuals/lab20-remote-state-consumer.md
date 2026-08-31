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
a published interface: rename `vpc_id` and every consumer's next plan breaks. Here the producer is
[Lab 16](lab16-workspaces.md), which left two state files behind, each holding a **real VPC** in a
different CIDR. So this is not a toy read: `upstream_vpc_id` returns the ID of a network that exists
in AWS right now, and an application stack would build its subnets and security groups against it.

Note what the consumer still does not do. It creates nothing, and it never calls AWS — it opens a
state file. That is the whole point of the pattern: values cross the boundary without either stack
gaining permission over the other's resources.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `data.terraform_remote_state.upstream` | Reads the lab 16 producer's state file | Free |
| Output `upstream_outputs` | The producer's entire output map | Free |
| Output `upstream_environment` | A single value reached into the map, the realistic pattern | Free |
| Output `upstream_vpc_id` | The producer's real VPC ID — the classic cross-stack value | Free |
| Output `upstream_vpc_cidr` | The producer's VPC CIDR, as a route or rule would need it | Free |

## Before you start

- [ ] [Lab 19 — State migration](lab19-state-migration.md) completed
- [ ] [Lab 16 — Workspaces](lab16-workspaces.md) applied in **both** its `default` and `dev`
      workspaces, and **not** destroyed — this lab reads the two state files it left behind
      (`default` in step 2, `dev` in step 9). Lab 16's cleanup section is deliberately deferred
      until after this lab; if you already ran it, reapply lab 16 steps 5 to 8 before continuing.
- [ ] Read [../docs/13-remote-state.md](../docs/13-remote-state.md)

This lab creates no resources and needs no AWS credentials of its own — it reads a local file. Lab 16
does need credentials, because its VPCs are real, so make sure those two VPCs still exist before you
start. The S3 producer variant is shown in step 9.

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

Read the contract before you consume it. These five names are everything this consumer can rely on.

```bash
terraform -chdir=../lab16-workspaces output
```

**Expected output**

```text
PENDING CAPTURE — rerun after credentials are restored
```

Five outputs: `labels`, `workspace`, `vpc_cidr`, `vpc_id` and `vpc_name`. `vpc_id` is a real
`vpc-` identifier. Everything else this consumer might want — a subnet ID, a route table ID — is
*not* on that list, and therefore not available, no matter that lab 16's state file contains it.
Only declared outputs cross the boundary.

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
PENDING CAPTURE — rerun after credentials are restored
```

Every value is already resolved rather than showing `(known after apply)`, including
`upstream_vpc_id`. The plan ends with `You can apply this plan to save these new output values to the
Terraform state, without changing any real infrastructure.`

### Step 7 — Apply and read the values

```bash
terraform apply -auto-approve
```

**Expected output**

```text
PENDING CAPTURE — rerun after credentials are restored
```

`Apply complete! Resources: 0 added, 0 changed, 0 destroyed.`

`0 added` confirms the consumer touched nothing — and it is worth sitting with that. This module now
holds the ID of a live VPC and could hand it to any resource that needs one, yet it created nothing,
modified nothing, and made no AWS API call at all.

`upstream_environment` reached two levels into the producer's `labels` map — indexing like that is
the contract at its most brittle. `upstream_vpc_id` reads a top-level output instead, which is why
that form is the one to prefer.

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
PENDING CAPTURE — rerun after credentials are restored
```

`upstream_environment` is now `"dev"`, and `upstream_vpc_id` is a **different** `vpc-` ID —
lab 16's `dev` VPC, at `10.17.0.0/16` rather than `10.16.0.0/16`. One variable changed and the
consumer is pointed at a different real network. That is how a single application stack is deployed
against a per-environment network stack.

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
`subnet_id` is a good example: lab 16 has no subnet, and even if it did, the value would not cross
this boundary unless someone declared an output for it.

```bash
terraform console
> data.terraform_remote_state.upstream.outputs.vpc_id
> data.terraform_remote_state.upstream.outputs.subnet_id
```

**Expected output**

```text
PENDING CAPTURE — rerun after credentials are restored
```

The first expression returns the VPC ID. The second fails:

```text
Error: Unsupported attribute

This object does not have an attribute named "subnet_id".
```

Type `exit` to leave the console. Now picture the same error arriving because someone renamed
`vpc_id` to `network_id` in the producer. Nothing is wrong with the producer — it applies cleanly, its
VPC is healthy — and yet the failure lands in the *consumer*. That asymmetry is why output names need
the same care as a public API.

## Done when

- [ ] `terraform -chdir=../lab16-workspaces output` showed the producer's five outputs
- [ ] `terraform plan` read the data source and resolved every output value, including `upstream_vpc_id`
- [ ] Apply reported `0 added, 0 changed, 0 destroyed`
- [ ] `upstream_vpc_id` matched a real VPC ID from lab 16
- [ ] `terraform state list` returned only the data source address
- [ ] Pointing at the `dev` workspace state changed `upstream_environment` to `"dev"` and
      `upstream_vpc_id` to lab 16's other VPC
- [ ] Requesting `subnet_id` produced `Unsupported attribute` while `vpc_id` succeeded
- [ ] You can explain why renaming a producer's output breaks its consumers

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `Error: Failed to read state file` / no such file | Lab 16 was destroyed or never applied | Apply lab 16 in its `default` workspace, then retry |
| `upstream_outputs = {}` | Producer state exists but has no outputs recorded | Reapply the producer; outputs are only stored on apply |
| `Unsupported attribute` on `outputs.labels` or `outputs.vpc_id` | Pointing at a producer that publishes different outputs, or lab 16 applied before it created a VPC | Check the path, then rerun step 3 against that directory; reapply lab 16 if its outputs are missing `vpc_id` |
| Reads the wrong environment | Pointing at `terraform.tfstate` instead of the workspace file | Named workspaces live under `terraform.tfstate.d/<name>/` |
| Consumer plan changes after a producer apply | The producer's output values moved | Expected: the consumer re-reads on every plan |
| `AccessDenied` with the S3 variant | No read permission on the producer's key | A policy boundary, not a config error — request `s3:GetObject` on that prefix |
| `Backend configuration changed` with the S3 variant | Switched `backend` inside the data source after init | Rerun `terraform init` |

## Cleanup

```bash
terraform destroy -auto-approve
```

Destroying the consumer does not affect the producer — lab 16's two VPCs are still running, which is
the last thing this lab demonstrates about the read-only nature of the data source.

Lab 16 is now safe to clean up, and it must be: those two VPCs are real. Return to its
[cleanup section](lab16-workspaces.md#cleanup) and run the commands you deferred, then confirm with
the `describe-vpcs` check there.

## Next steps

- Deep dive: [../docs/13-remote-state.md](../docs/13-remote-state.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab20-remote-state-consumer)
- Continue to [Lab 21 — Dynamic Blocks](lab21-dynamic-blocks.md)
