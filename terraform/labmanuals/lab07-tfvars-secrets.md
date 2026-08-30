# Lab 07 — tfvars and Secrets

| | |
|---|---|
| **Goal** | Supply variable values from a `terraform.tfvars` file, pass a secret through a `TF_VAR_` environment variable, see `sensitive = true` redact it, and work out which source wins when two disagree. |
| **Time** | 40–50 minutes |
| **Tier** | Intermediate |
| **Files** | `terraform/labs/lab07-tfvars-secrets/` |

## Overview

Lab 06 passed values with `-var` on the command line, which is fine for one value and painful for
ten. A **tfvars file** is a plain file of `name = value` lines that Terraform reads automatically
when it is called `terraform.tfvars`. That solves the typing problem but creates a new one: a file
of settings is exactly where people accidentally commit passwords.

This lab separates the two kinds of input. Ordinary settings go in `terraform.tfvars`. The secret
never touches a file — it arrives through the `TF_VAR_db_password` environment variable, and its
variable is marked `sensitive = true` so Terraform refuses to print it. You will then set the same
variable from two places at once to see the precedence order for yourself.

This lab creates nothing in AWS, so it costs nothing and needs no credentials.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| 3 plain variables | `project`, `environment`, `cost_code` — set from `terraform.tfvars` | Free |
| 1 sensitive variable | `db_password` — set from the environment | Free |
| 2 validation rules | Reject a bad `environment` or a bad `cost_code` | Free |
| 3 outputs | `settings`, `db_password` (redacted), `db_password_length` | Free |

## Before you start

- [ ] Lab 06 completed ([lab06-variables-outputs.md](lab06-variables-outputs.md))
- [ ] Working directory: `../labs/lab07-tfvars-secrets/` (no AWS credentials needed)

## Steps

### Step 1 — See what is and is not committed

```bash
cd terraform/labs/lab07-tfvars-secrets
ls
grep tfvars ../../../.gitignore
```

**Expected output**

```text
main.tf
outputs.tf
terraform.tfvars.example
variables.tf
```

```text
**/*.tfvars
!**/*.tfvars.example
```

There is no `terraform.tfvars` yet, only a `.example`. The repository ignores every `*.tfvars` file
and makes one exception for `*.tfvars.example`. So the real file with real values is never committed,
while a committed template shows the next person which variables exist. Every lab in this track that
takes variables ships a `terraform.tfvars.example` for that reason.

### Step 2 — Read the variable declarations

```bash
cat variables.tf
```

**Expected output**

```text
variable "project" {
  type        = string
  description = "Project name. Set in terraform.tfvars."
}
...
variable "db_password" {
  type        = string
  description = "Database password. Never put this in a committed file; export TF_VAR_db_password instead."
  sensitive   = true
}
```

None of the four variables has a `default`, so all four are mandatory. Only `db_password` carries
`sensitive = true`. Two of the others carry a `validation` block, which you will trip in Steps 13
and 14.

### Step 3 — Read the committed template

```bash
cat terraform.tfvars.example
```

**Expected output**

```text
# Copy to terraform.tfvars, then edit. terraform.tfvars is gitignored.
# This .example file is committed, so it must never contain a real secret.

project     = "platform"
environment = "dev"
cost_code   = "123"

# db_password is deliberately absent. Supply it at runtime:
#   export TF_VAR_db_password='not-a-real-password'
```

The template sets three variables and deliberately omits the fourth. A committed template that
listed `db_password = "..."` would defeat the whole point, so it documents the runtime method
instead.

### Step 4 — Create your real tfvars file

```bash
cp terraform.tfvars.example terraform.tfvars
```

Terraform loads a file named exactly `terraform.tfvars` on its own — you do not pass a flag for it.
Any other name needs `-var-file`.

### Step 5 — Initialize

```bash
terraform init
```

**Expected output**

```text
Terraform has been successfully initialized!
```

### Step 6 — Plan without the secret, and watch Terraform ask for it

```bash
terraform plan
```

**Expected output**

```text
var.db_password
  Database password. Never put this in a committed file; export TF_VAR_db_password instead.

  Enter a value:
```

Three variables came from `terraform.tfvars`, so Terraform does not ask about them. The fourth is
mandatory and unset, so Terraform prompts interactively and shows the variable's `description` — one
concrete reason every variable should have one. Press `Ctrl-C` to cancel rather than typing a value.

In a non-interactive context such as CI there is no prompt, and you get this instead:

```text
Error: No value for required variable

  on variables.tf line 26:
  26: variable "db_password" {

The root module input variable "db_password" is not set, and has no default
value.
```

### Step 7 — Supply the secret through the environment

```bash
export TF_VAR_db_password='not-a-real-password'
terraform plan
```

**Expected output**

```text
Changes to Outputs:
  + db_password        = (sensitive value)
  + db_password_length = 19
  + settings           = {
      + cost_code   = "123"
      + environment = "dev"
      + project     = "platform"
    }
```

Terraform reads any environment variable named `TF_VAR_` plus the variable name. The value lives
only in your shell session, so there is no file to leak and nothing to commit. No prompt this time.

### Step 8 — Apply and watch the redaction

```bash
terraform apply -auto-approve
```

**Expected output**

```text
Apply complete! Resources: 0 added, 0 changed, 0 destroyed.

Outputs:

db_password = <sensitive>
db_password_length = 19
settings = {
  "cost_code" = "123"
  "environment" = "dev"
  "project" = "platform"
}
```

`db_password` prints as `<sensitive>` because both the variable and the output are marked
`sensitive = true`. `db_password_length` is `19` — proof the value arrived, without showing it. That
output had to be wrapped in `nonsensitive()`, because anything derived from a sensitive value is
treated as sensitive too, and `terraform validate` refuses to expose it otherwise.

### Step 9 — Read the secret back out

```bash
terraform output -raw db_password
```

**Expected output**

```text
not-a-real-password
```

Asking for the value by name gives it to you. `sensitive = true` prevents accidental display in
plans, applies, and logs. It is not encryption and it is not access control.

### Step 10 — Find the secret in the state file

```bash
grep -o 'not-a-real-password' terraform.tfstate
```

**Expected output**

```text
not-a-real-password
```

You kept the secret out of git, and it landed in `terraform.tfstate` in clear text anyway. This is
why that file is gitignored too, and it is the problem Lab 08 examines in detail.

### Step 11 — Precedence: `-var` beats `terraform.tfvars`

```bash
terraform plan -var 'environment=prod'
```

**Expected output**

```text
Changes to Outputs:
  ~ settings           = {
      ~ environment = "dev" -> "prod"
        # (2 unchanged attributes hidden)
    }
```

`terraform.tfvars` says `dev`. The command line says `prod`. The command line wins.

### Step 12 — Precedence: `terraform.tfvars` beats `TF_VAR_`

```bash
TF_VAR_environment=prod terraform plan
```

**Expected output**

```text
No changes. Your infrastructure matches the configuration.
```

The environment variable said `prod`, and nothing changed — `terraform.tfvars` still won with `dev`.
This one surprises people, so learn the full order now, highest priority first:

1. `-var` on the command line
2. `-var-file` on the command line
3. `terraform.tfvars`
4. `TF_VAR_` environment variable
5. The variable's `default`

Note the consequence for secrets: because `TF_VAR_` sits *below* tfvars, a stale variable exported in
your shell will be silently ignored if someone adds the same name to `terraform.tfvars`.

### Step 13 — Trip the `environment` validation rule

```bash
terraform plan -var 'environment=Production'
```

**Expected output**

```text
Error: Invalid value for variable

  on variables.tf line 6:
   6: variable "environment" {
    ├────────────────
    │ var.environment is "Production"

environment must be dev, test, or prod.

This was checked by the validation rule at variables.tf:10,3-13.
```

A `validation` block inside a `variable` rejects bad input before Terraform contacts any provider.
The error quotes the offending value, prints your own `error_message`, and points at the rule.

### Step 14 — Trip the `cost_code` validation rule

```bash
terraform plan -var 'cost_code=12345'
```

**Expected output**

```text
Error: Invalid value for variable

  on variables.tf line 16:
  16: variable "cost_code" {
    ├────────────────
    │ var.cost_code is "12345"

cost_code must contain exactly three characters.
```

Validation is not limited to a fixed list of allowed values. This rule uses `length()`, and any
expression returning `true` or `false` will work.

### Step 15 — Clean up the secret and the tfvars file

```bash
terraform destroy -auto-approve
rm -f terraform.tfvars
unset TF_VAR_db_password
```

`rm` and `unset` matter here. Leaving a real `terraform.tfvars` on disk or a secret exported in your
shell is how the value ends up somewhere you did not intend.

## Done when

- [ ] `terraform.tfvars` exists locally and matches a `.gitignore` pattern
- [ ] A plan without `TF_VAR_db_password` prompts for it, naming the variable's description
- [ ] `apply` prints `db_password = <sensitive>` and `db_password_length = 19`
- [ ] `terraform output -raw db_password` prints the real value
- [ ] You found the same secret in clear text inside `terraform.tfstate`
- [ ] `-var 'environment=prod'` overrides the tfvars file, but `TF_VAR_environment=prod` does not
- [ ] Both validation rules reject bad input with your own error messages

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| Terraform prompts `Enter a value` | A mandatory variable is unset | `export TF_VAR_db_password='not-a-real-password'` |
| `No value for required variable` | Same, in a non-interactive shell | Export the variable, or pass `-var` |
| tfvars values ignored | File is named something else, e.g. `vars.tfvars` | Rename to `terraform.tfvars` or pass `-var-file` |
| `TF_VAR_` export seems to do nothing | The same name is set in `terraform.tfvars`, which wins | Remove it from tfvars, or use `-var` |
| `Output refers to sensitive values` | An output derives from a sensitive value | Add `sensitive = true`, or wrap in `nonsensitive()` |
| `environment must be dev, test, or prod` | Validation rule tripped | Use a lowercase value from the list |
| Secret appears in a committed file | Values put in `terraform.tfvars.example` | Move them to `terraform.tfvars` |

## Cleanup

```bash
terraform destroy -auto-approve
rm -f terraform.tfvars
unset TF_VAR_db_password
```

## Next steps

- Deep dive: [docs/05-variables.md](../docs/05-variables.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab07-tfvars-secrets)
- Continue to [Lab 08 — Local State](lab08-local-state.md)
