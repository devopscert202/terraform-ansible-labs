# Lab 16 — Workspaces

| | |
|---|---|
| **Goal** | Keep two independent copies of the same configuration side by side, each with its own state, and read the active workspace name from inside the code. |
| **Time** | 25–30 minutes |
| **Tier** | Advanced |
| **Files** | `terraform/labs/lab16-workspaces/` |

## Overview

Every Terraform directory you have used so far had exactly one state file, so applying the
configuration twice with different values would overwrite the first result. A **workspace** is a
named, separate state file for the same configuration directory. Switch workspace and Terraform
forgets the other workspace's resources entirely — the code is shared, the state is not.

Every directory starts with one workspace called `default`, which is why you have never had to
think about this. This lab creates a second workspace, applies in both, and reads the built-in
`terraform.workspace` value so resource names and tags can vary per environment.

Workspaces are lightweight: they give you separate state and nothing else — no separate AWS
account, no separate credentials, no approval gate. That limitation motivates the next two labs,
which use separate state keys instead.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `terraform_data.workspace` | Stores a label map built from the active workspace name | Free |
| Output `workspace` | The active workspace name | Free |
| Output `labels` | The label map, so you can see it change per workspace | Free |

## Before you start

- [ ] [Lab 15 — remote-exec provisioner](lab15-remote-exec-provisioner.md) completed
- [ ] Terraform 1.5.0 or newer (`terraform version`)
- [ ] Read the state model notes in [../docs/12-workspaces.md](../docs/13-remote-state.md)

No AWS resources and no credentials are needed.

## Steps

### Step 1 — Move into the lab directory and read the workspace reference

`terraform.workspace` is a built-in value, not a variable. It always holds the name of the active
workspace, so you never declare it and it needs no default.

```bash
cd terraform/labs/lab16-workspaces
cat main.tf
```

**Expected output**

```text
terraform { required_version = ">= 1.5.0" }

locals {
  environment = terraform.workspace
  labels      = { environment = terraform.workspace, managed_by = "terraform" }
}

resource "terraform_data" "workspace" { input = local.labels }
output "workspace" { value = terraform.workspace }
output "labels" { value = terraform_data.workspace.output }
```

### Step 2 — Initialize

```bash
terraform init
```

**Expected output**

```text
Initializing provider plugins...
- terraform.io/builtin/terraform is built in to Terraform

Terraform has been successfully initialized!
```

### Step 3 — Validate the configuration

```bash
terraform validate
```

**Expected output**

```text
Success! The configuration is valid.
```

### Step 4 — Confirm which workspace you are in

Every directory starts in `default`. The asterisk in `workspace list` marks the active one.

```bash
terraform workspace show
terraform workspace list
```

**Expected output**

```text
default
* default
```

### Step 5 — Apply in the default workspace

```bash
terraform apply -auto-approve
```

**Expected output**

```text
  # terraform_data.workspace will be created
  + resource "terraform_data" "workspace" {
      + id     = (known after apply)
      + input  = {
          + environment = "default"
          + managed_by  = "terraform"
        }
      + output = (known after apply)
    }

Plan: 1 to add, 0 to change, 0 to destroy.

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

labels = {
  "environment" = "default"
  "managed_by" = "terraform"
}
workspace = "default"
```

`terraform.workspace` resolved to `default`, so that is what landed in the label map.

### Step 6 — Create and switch to a second workspace

`workspace new` creates the workspace and switches to it in one step.

```bash
terraform workspace new dev
```

**Expected output**

```text
Created and switched to workspace "dev"!

You're now on a new, empty workspace. Workspaces isolate their state,
so if you run "terraform plan" Terraform will not see any existing state
for this configuration.
```

### Step 7 — Prove the new workspace's state is empty

You applied a resource moments ago, yet this workspace cannot see it. That is the isolation the
whole feature exists to provide.

```bash
terraform state list
```

**Expected output**

```text
No state file was found!

State management commands require a state file. Run this command
in a directory where Terraform has been run or use the -state flag
to point the command to a specific state location.
```

### Step 8 — Apply in the new workspace

The command is identical to step 5, but it acts on different state and produces a different
result — which is why it is a separate operation, not a repeat.

```bash
terraform apply -auto-approve
```

**Expected output**

```text
  # terraform_data.workspace will be created
  + resource "terraform_data" "workspace" {
      + id     = (known after apply)
      + input  = {
          + environment = "dev"
          + managed_by  = "terraform"
        }
      + output = (known after apply)
    }

Plan: 1 to add, 0 to change, 0 to destroy.

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

labels = {
  "environment" = "dev"
  "managed_by" = "terraform"
}
workspace = "dev"
```

Terraform created a *second* resource rather than modifying the first. The two workspaces do not
know about each other.

### Step 9 — List the workspaces

```bash
terraform workspace list
```

**Expected output**

```text
  default
* dev
```

### Step 10 — Find the state files on disk

This layout matters in lab 20, where another module reads one of these files directly by path.

```bash
find . -name '*.tfstate' -not -path './.terraform/*'
```

**Expected output**

```text
./terraform.tfstate
./terraform.tfstate.d/dev/terraform.tfstate
```

The `default` workspace keeps the plain `terraform.tfstate`; every named workspace gets its own
file under `terraform.tfstate.d/<name>/`.

### Step 11 — Switch back and confirm the first workspace survived

```bash
terraform workspace select default
terraform output
```

**Expected output**

```text
Switched to workspace "default".
labels = {
  "environment" = "default"
  "managed_by" = "terraform"
}
workspace = "default"
```

Switching workspaces changed nothing on either side — both states still exist independently.

## Done when

- [ ] `terraform workspace list` shows both `default` and `dev`
- [ ] `terraform state list` in the fresh `dev` workspace reported no state file
- [ ] The `labels` output read `environment = "dev"` in `dev` and `"default"` in `default`
- [ ] Both state files exist at the paths shown in step 10
- [ ] You can state one thing workspaces isolate and one thing they do not
- [ ] You have **not** run the cleanup commands — lab 20 needs both state files

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `Workspace "dev" already exists` | The workspace was created in an earlier attempt | Use `terraform workspace select dev` instead of `new` |
| Plan shows resources you thought you destroyed | You are in a different workspace than you expect | Run `terraform workspace show` before every plan |
| `Currently selected workspace "dev" does not exist` | State directory was deleted while `dev` was active | `terraform workspace select default`, then recreate `dev` |
| `terraform output` prints nothing | The active workspace has never been applied | Apply in that workspace first |
| `Cannot delete the currently selected workspace` | Tried to delete the active workspace | Select `default` first, then `terraform workspace delete dev` |
| `Workspace is not empty` on delete | The workspace still has resources in state | Destroy in that workspace before deleting it |

## Cleanup

**Do not run this yet.** [Lab 20](lab20-remote-state-consumer.md) reads both state files this lab
just created — the `default` one in its step 2 and the `dev` one in its step 9. Destroying here
makes lab 20 fail with `Failed to read state file`.

Nothing in this lab is an AWS resource, so leaving it in place costs nothing. Return here after
lab 20 and run the following. Each workspace must be destroyed separately — destroying one leaves
the other untouched.

```bash
terraform workspace select dev
terraform destroy -auto-approve
terraform workspace select default
terraform destroy -auto-approve
terraform workspace delete dev
```

## Next steps

- Deep dive: [../docs/13-remote-state.md](../docs/13-remote-state.md)
- Visual: [../html/advanced.html](../html/advanced.html)
- Continue to [Lab 17 — S3 backend](lab17-s3-backend.md)
