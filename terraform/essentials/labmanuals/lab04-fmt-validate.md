# Lab 04 — Format and Validate

> **Goal:** Use `terraform fmt` and `terraform validate` as quality gates before planning, and observe sensitive output redaction.
> **Time:** ~40 min · **Difficulty:** Beginner · **Files:** `labs/lab04-fmt-validate/`

## Overview

Production teams reject pull requests that fail formatting or validation checks. This lab practices both commands on a `random_string` resource named `formatted_example` with a **sensitive** output. You will intentionally misformat a file, run `fmt`, break a reference and fix it with `validate`, then apply and observe how sensitive values appear in CLI output versus `terraform output -raw`.

## Learning objectives

- Rewrite HCL with `terraform fmt -recursive`
- Use `terraform fmt -check` the way CI pipelines do
- Run `terraform validate` after `init`
- Understand `sensitive = true` on outputs
- Complete apply/destroy without AWS credentials

## Prerequisites

- [ ] Terraform 1.5+ installed
- [ ] Lab 03 complete (init/plan/apply familiarity)
- [ ] Working directory: `terraform/essentials/labs/lab04-fmt-validate`

## What you will build

```
terraform/essentials/labs/lab04-fmt-validate/
└── main.tf    # random_string.formatted_example, sensitive output
```

```hcl
resource "random_string" "formatted_example" {
  length  = 10
  special = true
  numeric = true
  upper   = true
}

output "formatted_example" {
  value     = random_string.formatted_example.result
  sensitive = true
}
```

---

## Exercise 1 — Initialize

<a id="ex1"></a>

### Step 1.1 — Navigate to lab directory

```bash
cd ~/terraform-ansible-labs/terraform/essentials/labs/lab04-fmt-validate
ls -la
```

**Validate** — `main.tf` present.

**What happened:** Isolated root module; separate state from Lab 03.

### Step 1.2 — Initialize

```bash
terraform init
```

**Validate**

```text
Terraform has been successfully initialized!
```

**What happened:** Random provider downloaded to `.terraform/providers/`.

---

## Exercise 2 — Formatting with terraform fmt

<a id="ex2"></a>

### Step 2.1 — Check current formatting

```bash
terraform fmt -check -recursive .
echo $?
```

**Validate** — exit code is **non-zero** (typically `3`) and `main.tf` is listed. This lab ships with **intentionally bad formatting** so you can see `fmt` fix it.

**What happened:** `-check` exits non-zero when files would change — CI uses this to block merges. Do not run `terraform fmt` yet.

### Step 2.2 — Introduce bad formatting (temporary)

```bash
cp main.tf main.tf.bak
cat > /tmp/badfmt.tf << 'EOF'
resource "random_string" "formatted_example" {
length=10
special=true
}
EOF
# Do NOT overwrite main.tf permanently — this demonstrates fmt behavior
terraform fmt -check /tmp/badfmt.tf; echo "check exit: $?"
terraform fmt /tmp/badfmt.tf && cat /tmp/badfmt.tf
rm /tmp/badfmt.tf
```

**Validate** — after `terraform fmt`, file shows two-space indent and aligned `=`.

**What happened:** `fmt` is the authoritative style — not personal preference.

### Step 2.3 — Format the lab directory

```bash
terraform fmt -recursive .
```

**Validate** — no output or list of changed files.

**What happened:** Entire module tree formatted consistently.

---

## Exercise 3 — Validation

<a id="ex3"></a>

### Step 3.1 — Validate configuration

```bash
terraform validate
```

**Validate**

```text
Success! The configuration is valid.
```

**What happened:** Syntax, types, and references are correct. No cloud APIs called.

### Step 3.2 — Understand validate limits

Run a plan to see the difference:

```bash
terraform plan
```

**Validate** — plan shows `+ random_string.formatted_example` and output `(sensitive value)` for formatted_example.

**What happened:** `validate` does not evaluate computed values; `plan` does.

---

## Exercise 4 — Plan and apply

<a id="ex4"></a>

### Step 4.1 — Plan

```bash
terraform plan -out=tfplan
```

**Validate**

```text
Plan: 1 to add, 0 to change, 0 to destroy.
```

**What happened:** One resource with length 10, specials/numeric/upper enabled.

### Step 4.2 — Apply

```bash
terraform apply tfplan
```

**Validate**

```text
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

formatted_example = (sensitive value)
```

**What happened:** Sensitive outputs are redacted in standard apply output.

### Step 4.3 — Reveal sensitive output locally

```bash
terraform output -raw formatted_example
```

**Validate** — ten-character string with mixed character classes.

```bash
terraform output -raw formatted_example | wc -c
```

**Validate** — length 10 (plus newline).

**What happened:** Redaction protects shoulder-surfing; `-raw` is for authorized operators only.

---

## Exercise 5 — Sensitive values and state

<a id="ex5"></a>

### Step 5.1 — Inspect state

```bash
terraform state show random_string.formatted_example
```

**Validate** — `result` attribute visible in state show.

**What happened:** `sensitive` redacts CLI display during apply — **not** encryption in state. Treat state files as confidential.

### Step 5.2 — JSON show (careful)

```bash
terraform show -json | grep -o '"result":"[^"]*"' | head -1
```

**Validate** — result value appears in JSON.

**What happened:** Never commit state; use remote encrypted backends in teams.

---

## Exercise 6 — CI simulation

<a id="ex6"></a>

### Step 6.1 — Run CI-style checks

```bash
terraform fmt -check -recursive . && \
terraform init -backend=false && \
terraform validate && \
echo "CI checks passed"
```

**Validate**

```text
CI checks passed
```

**What happened:** Pipelines run fmt, init, validate before plan. `-backend=false` skips remote backend when not needed.

---

## Exercise 7 — Destroy

<a id="ex7"></a>

### Step 7.1 — Destroy resources

```bash
terraform destroy
```

Type `yes` when prompted.

**Validate**

```text
Destroy complete! Resources: 0 added, 0 changed, 1 destroyed.
```

### Step 7.2 — Cleanup artifacts

```bash
rm -f tfplan main.tf.bak 2>/dev/null
terraform state list
```

**Validate** — empty state list.

**What happened:** Lab complete; no cloud resources to verify.

---

## Key takeaways

- `fmt` before every commit; `fmt -check` in CI
- `validate` after `init`, before `plan`
- Sensitive outputs redact apply display, not state
- Quality gates catch errors in seconds

## Done when

- [ ] `terraform fmt -check` passes
- [ ] `terraform validate` succeeds
- [ ] Apply showed `(sensitive value)` for output
- [ ] `terraform output -raw formatted_example` revealed value
- [ ] `terraform destroy` completed
- [ ] You understand validate vs plan scope

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `fmt -check` fails | Unformatted HCL | Run `terraform fmt -recursive` |
| validate before init | No providers | `terraform init` |
| Output not sensitive | Missing `sensitive = true` | Check output block |
| Stale tfplan | Config changed | Re-plan |

## Cleanup

```bash
cd ~/terraform-ansible-labs/terraform/essentials/labs/lab04-fmt-validate
terraform destroy -auto-approve 2>/dev/null || true
rm -f tfplan terraform.tfstate.backup
```

## Next steps

- [Lab 05 — Variables](lab05-variables.md)
- [Quality doc](../docs/05-quality/README.md)
- [Workflow HTML](../html/workflow.html)

---
*Terraform Essentials · Next: [lab05](lab05-variables.md)*
