# Lab 04 — Plan, Apply, and Destroy

| | |
|---|---|
| **Goal** | Run the complete Terraform lifecycle end to end, and see how Terraform remembers what it already built. |
| **Time** | 25–35 minutes |
| **Tier** | Basic |
| **Files** | `../labs/lab04-plan-apply-destroy/` |

## Overview

[Lab 03](lab03-first-ec2.md) ran the core commands against a real, billable server. This lab
runs the same cycle — `init`, `plan`, `apply`, `destroy` — on a resource that costs nothing and
needs no AWS credentials, so you can concentrate on the workflow rather than on the cloud.

The resource is a random twelve-character string, but the point of the lab is what happens
between the commands. After `apply`, Terraform writes a file called `terraform.tfstate`
recording what it created, and every later `plan` compares your configuration against that
record. That comparison is why running `plan` twice gives different answers, and why Terraform
destroys exactly what it made and nothing else.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `random_string.example` | A twelve-character lowercase string | None |
| Output `generated_value` | Prints the string after apply | None |
| `terraform.tfstate` | Terraform's record of what it created | None |

## Before you start

- [ ] [Lab 03](lab03-first-ec2.md) completed
- [ ] No AWS credentials needed — this lab never contacts AWS

## Steps

### Step 1 — Initialize the lab directory

```bash
cd terraform/labs/lab04-plan-apply-destroy
terraform init
```

**Expected output**

```text
- Finding hashicorp/random versions matching "~> 3.0"...
- Installing hashicorp/random v3.9.0...
- Installed hashicorp/random v3.9.0 (signed by HashiCorp)

Terraform has been successfully initialized!
```

### Step 2 — Read the configuration

```bash
cat main.tf
```

There is no `provider "aws"` block and no region, because the random provider runs entirely on
your machine. `resource "random_string" "example"` gives the type first, then a label you
choose. Together they form the address `random_string.example` used in plans, in state, and in
the output block at the bottom of the file.

### Step 3 — Plan the change

```bash
terraform plan
```

**Expected output**

```text
  # random_string.example will be created
  + resource "random_string" "example" {
      + length  = 12
      + lower   = true
      + result  = (known after apply)
      + special = false
      + upper   = false
    }

Plan: 1 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + generated_value = (known after apply)
```

Terraform has no record of this resource, so it proposes creating one. The `+` symbol marks a
creation, and `(known after apply)` marks a value that does not exist until the resource does.
Nothing has been created yet — `plan` only reports.

### Step 4 — Apply the change

```bash
terraform apply
```

Terraform reprints the plan and waits. Type `yes` and press Enter.

**Expected output**

```text
random_string.example: Creating...
random_string.example: Creation complete after 0s [id=itrcs1d4qj44]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

generated_value = "itrcs1d4qj44"
```

Your string will differ. `terraform.tfstate` now exists in the directory.

### Step 5 — Read the value back

Outputs are stored, not just printed, so you can read them back at any time.

```bash
terraform output generated_value
```

**Expected output**

```text
"itrcs1d4qj44"
```

### Step 6 — Plan a second time

This is the step that matters. Nothing about your configuration changed, so run `plan` again.

```bash
terraform plan
```

**Expected output**

```text
No changes. Your infrastructure matches the configuration.

Terraform has compared your real infrastructure against your configuration
and found no differences, so no changes are needed.
```

The first plan proposed a creation; this one proposes nothing, and the only difference is the
state file. Terraform is comparing what you asked for against what it recorded. `No changes` is
the normal steady state of a healthy configuration.

### Step 7 — Destroy the resource

```bash
terraform destroy
```

Terraform lists what will be removed and waits. Type `yes`.

**Expected output**

```text
random_string.example: Destroying... [id=itrcs1d4qj44]
random_string.example: Destruction complete after 0s

Destroy complete! Resources: 1 destroyed.
```

### Step 8 — Confirm nothing is left

```bash
terraform state list
```

The command prints nothing. An empty state means Terraform manages nothing here, and a fresh
`plan` would again propose creating the string. [Lab 08](lab08-local-state.md) examines state.

## Done when

- [ ] The first `plan` showed `1 to add`
- [ ] `apply` printed a value for `generated_value`
- [ ] The second `plan` reported `No changes`
- [ ] `destroy` reported `1 destroyed`
- [ ] `terraform state list` prints nothing

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `Could not load plugin` | `init` not run in this directory | Run `terraform init` |
| Second plan still shows `1 to add` | The apply was not confirmed with `yes` | Re-run `terraform apply` |
| `Error asking for approval` | Terminal cannot accept input | Use `terraform apply -auto-approve` |
| A different string each apply | Expected — the value is random | No action needed |
| `Error acquiring the state lock` | Another Terraform process is running | Wait for it to finish, then retry |
| `destroy` reports `0 destroyed` | Already destroyed | Confirm with `terraform state list` |

## Cleanup

```bash
terraform destroy
```

The state file is left behind deliberately so you can inspect it. Removing it is optional, and
safe only once `destroy` has finished:

```bash
rm -f terraform.tfstate terraform.tfstate.backup
```

## Next steps

- Deep dive: [The core workflow](../docs/03-workflow.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab04-plan-apply-destroy)
- Continue to [Lab 05 — Format and Validate](lab05-fmt-validate.md)
