# Lab 14 — local-exec provisioner

| | |
|---|---|
| **Goal** | Run a shell command on your own machine as part of `terraform apply`, and see why HashiCorp calls this a last resort. |
| **Time** | 20–25 minutes |
| **Tier** | Advanced |
| **Files** | `terraform/labs/lab14-local-exec-provisioner/` |

## Overview

A **provisioner** is a block you attach to a resource to run a script when that resource is
created or destroyed. `local-exec` runs the command on the machine running Terraform — your
laptop or a CI runner — not on any remote server.

HashiCorp's own documentation calls provisioners **a last resort**, because Terraform cannot see
what a shell command did: its effects are invisible to the plan, absent from state, and not
reversible. Prefer cloud-init or user-data for server setup and a real provider for API calls.
You still need to recognise them, though, because older modules are full of them.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `terraform_data.local_action` | A resource with no cloud counterpart, used purely to hang a provisioner on | Free |
| `local-exec` provisioner | Runs `printf` on your machine during create | Free |
| Output `message` | Echoes the string that was printed | Free |

`terraform_data` is a built-in resource that stores a value and nothing more — the standard way
to attach a provisioner when there is no real infrastructure to attach it to. No AWS credentials
are needed.

## Before you start

- [ ] [Lab 13 — Multi-provider configuration](lab13-multi-provider.md) completed
- [ ] Terraform 1.5.0 or newer (`terraform version`)
- [ ] A POSIX shell (`/bin/sh`) available — this lab does not run on Windows `cmd`
- [ ] Read [../docs/advanced/provisioners.md](../docs/advanced/provisioners.md)

## Steps

### Step 1 — Move into the lab directory

This lab is a single file — there are no variables or outputs files to read.

```bash
cd terraform/labs/lab14-local-exec-provisioner
ls
```

**Expected output**

```text
main.tf
```

### Step 2 — Read the provisioner block

Inside a provisioner, `self` refers to the resource it is attached to. `self` is not valid
anywhere else in Terraform.

```bash
grep -A4 'provisioner "local-exec"' main.tf
```

**Expected output**

```text
  provisioner "local-exec" {
    command = "printf '%s\n' '${self.input}'"
  }
}
```

### Step 3 — Initialize

`terraform_data` is built into Terraform, so there is no plugin to download from the registry.

```bash
terraform init
```

**Expected output**

```text
Initializing provider plugins...
- terraform.io/builtin/terraform is built in to Terraform

Terraform has been successfully initialized!
```

### Step 4 — Validate the configuration

```bash
terraform validate
```

**Expected output**

```text
Success! The configuration is valid.
```

### Step 5 — Plan, and notice what is missing

```bash
terraform plan
```

**Expected output**

```text
Terraform will perform the following actions:

  # terraform_data.local_action will be created
  + resource "terraform_data" "local_action" {
      + id     = (known after apply)
      + input  = "local-exec completed"
      + output = (known after apply)
    }

Plan: 1 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + message = (known after apply)
```

The plan says nothing about the `printf` command. This is the core weakness of provisioners:
Terraform cannot preview a shell command, so you get no warning about what it will do.

### Step 6 — Apply and watch the command run

```bash
terraform apply -auto-approve
```

**Expected output**

```text
terraform_data.local_action: Creating...
terraform_data.local_action: Provisioning with 'local-exec'...
terraform_data.local_action (local-exec): Executing: ["/bin/sh" "-c" "printf '%s\n' 'local-exec completed'"]
terraform_data.local_action (local-exec): local-exec completed
terraform_data.local_action: Creation complete after 0s [id=c0bf3dd9-90a7-e921-8113-b5421a7bc1c1]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

message = "local-exec completed"
```

Terraform prints the full command line it handed to `/bin/sh`. Your `id` will be a different
UUID.

### Step 7 — Apply again and confirm the command does not rerun

A create-time provisioner runs **once**, when the resource is created. Nothing prints this time.

```bash
terraform apply -auto-approve
```

**Expected output**

```text
terraform_data.local_action: Refreshing state... [id=c0bf3dd9-90a7-e921-8113-b5421a7bc1c1]

No changes. Your infrastructure matches the configuration.

Apply complete! Resources: 0 added, 0 changed, 0 destroyed.

Outputs:

message = "local-exec completed"
```

### Step 8 — Change the input; the command still does not run

This is the part that surprises people. Changing `input` is an *update*, not a replacement, so
the create-time provisioner does not fire even though the value changed.

```bash
terraform apply -auto-approve -var='message=second run'
```

**Expected output**

```text
  # terraform_data.local_action will be updated in-place
  ~ resource "terraform_data" "local_action" {
        id     = "c0bf3dd9-90a7-e921-8113-b5421a7bc1c1"
      ~ input  = "local-exec completed" -> "second run"
      ~ output = "local-exec completed" -> (known after apply)
    }

Plan: 0 to add, 1 to change, 0 to destroy.

terraform_data.local_action: Modifying... [id=c0bf3dd9-90a7-e921-8113-b5421a7bc1c1]
terraform_data.local_action: Modifications complete after 0s

Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

Outputs:

message = "second run"
```

The output value changed and no provisioner line appeared anywhere in that apply.

### Step 9 — Force a replacement to rerun the command

`-replace` tells Terraform to destroy and recreate a specific resource. Because the resource is
created again, the create-time provisioner fires again.

```bash
terraform apply -auto-approve -replace=terraform_data.local_action -var='message=second run'
```

**Expected output**

```text
  # terraform_data.local_action will be replaced, as requested
-/+ resource "terraform_data" "local_action" {
      ~ id     = "c0bf3dd9-90a7-e921-8113-b5421a7bc1c1" -> (known after apply)
      ~ output = "second run" -> (known after apply)
        # (1 unchanged attribute hidden)
    }

Plan: 1 to add, 0 to change, 1 to destroy.

terraform_data.local_action: Destroying... [id=c0bf3dd9-90a7-e921-8113-b5421a7bc1c1]
terraform_data.local_action: Destruction complete after 0s
terraform_data.local_action: Creating...
terraform_data.local_action: Provisioning with 'local-exec'...
terraform_data.local_action (local-exec): second run

Apply complete! Resources: 1 added, 0 changed, 1 destroyed.
```

Destroying and recreating real infrastructure just to rerun a script is rarely acceptable — the
practical reason to keep setup logic out of provisioners.

## Done when

- [ ] The first apply printed `local-exec completed` in the provisioner output lines
- [ ] `terraform plan` showed the resource but never mentioned the `printf` command
- [ ] The second, unchanged apply reported `0 added, 0 changed, 0 destroyed` and printed nothing
- [ ] Changing `message` updated the resource in place and still printed nothing
- [ ] `-replace` destroyed, recreated, and reran the command
- [ ] You can name one fair use of `local-exec` and one that belongs in user-data instead

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `Error running command ... exit status 127` | The command is not on `PATH` in the shell Terraform spawned | Use an absolute path in `command`, or test the command in your shell first |
| Provisioner output never appears | The resource already exists, so create-time provisioners are skipped | Use `-replace` as in step 9, or `terraform destroy` first |
| `Invalid reference: self` | `self` was used outside a provisioner or connection block | `self` is only valid inside those blocks; reference the resource by name elsewhere |
| Resource is left `tainted` after a failure | A create-time provisioner exited non-zero | Fix the command, then apply again — Terraform replaces tainted resources |
| Works in your shell but not in Terraform | Terraform uses `/bin/sh`, not your interactive shell | Avoid shell-specific syntax, or call `bash -c` explicitly |
| `-replace` reports no such resource | Resource address typo | Copy the exact address from `terraform state list` |

## Cleanup

```bash
terraform destroy -auto-approve
```

## Next steps

- Deep dive: [../docs/advanced/provisioners.md](../docs/advanced/provisioners.md)
- Visual: [../html/advanced.html](../html/advanced.html)
- Continue to [Lab 15 — remote-exec provisioner](lab15-remote-exec-provisioner.md)
