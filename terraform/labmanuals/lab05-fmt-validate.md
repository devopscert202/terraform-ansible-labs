# Lab 05 — Format and Validate

| | |
|---|---|
| **Goal** | Catch style and correctness problems with `terraform fmt` and `terraform validate` before a plan ever runs, and see exactly how far a sensitive output is hidden. |
| **Time** | 35–45 minutes |
| **Tier** | Basic |
| **Files** | `../labs/lab05-fmt-validate/` |

## Overview

Two commands check a configuration without touching any cloud. `terraform fmt` rewrites your
files into Terraform's standard layout — indentation and alignment only, never meaning.
`terraform validate` reports real mistakes: a misspelled argument, a missing brace, or a
reference to something that does not exist. Both are instant and free, and together they are the
gate most teams run automatically on every change.

You will break this configuration deliberately, twice — once for formatting and once for
correctness — and repair it each time, so you see what each command reports and what it misses.
The lab also introduces a **sensitive** output, one Terraform hides from casual display, and
ends with the three-command check a pipeline runs on every pull request.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `terraform_data.validation_probe` | Stores a value in state without calling any API | None |
| `random_string.formatted_example` | A ten-character string with mixed characters | None |
| Output `validation_probe` | An ordinary, visible output | None |
| Output `formatted_example` | The same idea, marked `sensitive = true` | None |

## Before you start

- [ ] [Lab 04](lab04-plan-apply-destroy.md) completed
- [ ] No AWS credentials needed — nothing here contacts AWS

## Steps

### Step 1 — Initialize the lab directory

```bash
cd terraform/labs/lab05-fmt-validate
terraform init
```

**Expected output**

```text
- Installing hashicorp/random v3.9.0...

Terraform has been successfully initialized!
```

### Step 2 — Break the formatting on purpose

Open `main.tf` and remove the indentation from the `length = 10` line inside
`random_string.formatted_example`, so it sits hard against the left margin. Then ask Terraform to
check the formatting without changing anything.

```bash
terraform fmt -check
echo "exit code: $?"
```

**Expected output**

```text
main.tf
exit code: 3
```

`-check` reports rather than repairs: it prints every badly formatted filename and exits
non-zero, which is what makes an automated pipeline stop. Note the code is `3`, not `1`.

### Step 3 — Repair the formatting

Run the same command without `-check`.

```bash
terraform fmt
```

**Expected output**

```text
main.tf
```

Here the filename means the opposite of what it meant in Step 2: this file was rewritten.

### Step 4 — Confirm the formatting is clean

```bash
terraform fmt -check
echo "exit code: $?"
```

**Expected output**

```text
exit code: 0
```

No filenames and an exit code of `0` means every file is already canonical. `fmt` never changes
what a configuration does, so it is safe to run at any time.

### Step 5 — Validate the configuration

```bash
terraform validate
```

**Expected output**

```text
Success! The configuration is valid.
```

### Step 6 — Break a reference and validate again

Formatting and correctness are different problems, and `fmt` cannot detect the second. In
`main.tf`, change the `formatted_example` output to read
`value = random_string.nonexistent.result`.

```bash
terraform validate
```

**Expected output**

```text
Error: Reference to undeclared resource

  on main.tf line 36, in output "formatted_example":
  36:   value       = random_string.nonexistent.result

A managed resource "random_string" "nonexistent" has not been declared in the
root module.
```

Terraform names the file, the line, and the reason. Note that `terraform fmt` would still pass
on this file: the layout is perfect and the meaning is broken.

### Step 7 — Restore the reference

Change the line back to `value = random_string.formatted_example.result`, then validate again.
Do not continue until this succeeds.

```bash
terraform validate
```

**Expected output**

```text
Success! The configuration is valid.
```

### Step 8 — Apply the configuration

Type `yes` when prompted.

```bash
terraform apply
```

**Expected output**

```text
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

formatted_example = <sensitive>
validation_probe = "terraform-labs"
```

`sensitive = true` replaced the random string with `<sensitive>`, while the ordinary output
printed normally.

### Step 9 — List the outputs

```bash
terraform output
```

**Expected output**

```text
formatted_example = <sensitive>
validation_probe = "terraform-labs"
```

Listing all outputs redacts the sensitive one the same way the apply summary did.

### Step 10 — Ask for the sensitive value by name

```bash
terraform output formatted_example
```

**Expected output**

```text
"4$fqJ-M&e2"
```

Your string will differ. This is the important detail: naming the output prints it in full,
because you asked for it directly. Redaction stops a secret appearing by accident in a shared
terminal or a build log — it is not a security boundary. The value is stored in plain text in
`terraform.tfstate` regardless, and `terraform output -json` returns it in full as well.

### Step 11 — List what state is tracking

```bash
terraform state list
```

**Expected output**

```text
random_string.formatted_example
terraform_data.validation_probe
```

### Step 12 — Inspect one entry in detail

```bash
terraform state show terraform_data.validation_probe
```

**Expected output**

```text
# terraform_data.validation_probe:
resource "terraform_data" "validation_probe" {
    id     = "bebaf852-03ad-e834-a6e7-1149a27e30ab"
    input  = "terraform-labs"
    output = "terraform-labs"
}
```

`terraform_data` exists only to hold a value in state. It calls no API, which makes it a safe way
to practise state commands without creating anything.

### Step 13 — Run the checks the way a pipeline does

These three commands are the standard gate on a pull request. `-recursive` covers every
subdirectory; `-backend=false` lets validation run without access to any remote state, which
matters on a build agent that has no credentials.

```bash
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

If all three exit `0`, the configuration is ready for someone to review a plan.

## Done when

- [ ] `terraform fmt -check` exited `3` on the unformatted file, then `0` after `terraform fmt`
- [ ] `terraform validate` reported the undeclared resource, then succeeded after the fix
- [ ] `apply` displayed `formatted_example = <sensitive>` and `2 added`
- [ ] `terraform output formatted_example` printed the real value
- [ ] `terraform state list` showed both resources
- [ ] `terraform destroy` reported `2 destroyed`

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `validate` fails before `init` | Provider schemas not downloaded | Run `terraform init` first |
| `fmt -check` still prints a filename | The file was edited again after `fmt` | Run `terraform fmt` once more |
| Validate error persists after the fix | The file was not saved | Save `main.tf`, then re-run |
| Error points at a line you did not edit | An unbalanced brace above it | Read the reported line, then check the braces |
| `terraform output` prints nothing | `apply` has not run yet | Run `terraform apply` |
| `state show` reports no instance found | The address is misspelled | Copy it from `terraform state list` |

## Cleanup

```bash
terraform destroy
```

```bash
rm -f terraform.tfstate terraform.tfstate.backup
```

## Next steps

- Deep dive: [Quality checks](../docs/04-quality.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab05-fmt-validate)
- Continue to [Lab 06 — Variables and Outputs](lab06-variables-outputs.md)
