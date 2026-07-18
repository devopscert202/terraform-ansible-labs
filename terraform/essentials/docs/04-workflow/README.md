# Terraform Core Workflow

## Objective (conceptual)

Terraform's daily loop is **init → fmt → validate → plan → apply → (eventually) destroy**. Each command has a distinct job: `init` prepares plugins and backends; `plan` is a dry-run diff; `apply` commits changes; `destroy` removes managed resources. Treat `plan` as mandatory review—especially before any command that bills a cloud account.

The mental model is **propose then commit**, like code review for infrastructure. State bridges configuration and reality; the workflow always compares `.tf` files to state and refreshes from the API before planning.

**Interactive reference:** [Core Workflow](../../html/workflow.html)

## Command responsibilities

| Command | Purpose |
|---------|---------|
| `terraform init` | Download providers, configure backend, create `.terraform/` |
| `terraform fmt` | Format `.tf` files to canonical style |
| `terraform validate` | Check syntax and internal consistency (no cloud calls) |
| `terraform plan` | Show create/update/destroy actions |
| `terraform apply` | Execute the plan (prompts unless `-auto-approve`) |
| `terraform destroy` | Tear down all managed resources in the directory |

## Lab 03: plan and apply cycle

```hcl
resource "random_string" "example" {
  length  = 12
  special = false
  upper   = false
}

output "generated_value" {
  value = random_string.example.result
}
```

Typical first apply output: `Plan: 1 to add, 0 to change, 0 to destroy`. After apply, `terraform.tfstate` records the resource ID.

## Lab 04: fmt and validate

Lab 04 ships intentionally messy formatting—run `terraform fmt` to normalize indentation:

```hcl
terraform {
required_version = ">= 1.5.0"
  required_providers {
    random = {
  source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

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

`sensitive = true` on an output redacts the value in normal CLI output but does not remove it from state.

## Safe apply habits

- Run from **one lab directory** at a time—each has isolated state.
- Read the plan summary line: `Plan: X to add, Y to change, Z to destroy`.
- For AWS labs, run `destroy` when finished to stop charges.
- Use `terraform plan -out=tfplan` in CI; `terraform apply tfplan` applies exactly that plan.

## State file appearance

After first `apply`, `terraform.tfstate` maps addresses like `random_string.example` to provider-assigned attributes. Do not hand-edit state; use `terraform state` subcommands if correction is needed.

## When to re-run init

- New or changed `required_providers`
- Backend configuration changes
- Cloning the repo on a new machine

## Plan flags (reference)

- `-destroy` — Plan teardown instead of forward changes.
- `-target=RESOURCE` — Limit scope (debug only; avoid in production pipelines).
- `-var='name=value'` — Override a variable at plan time.

## Saving and reusing plans

```bash
terraform plan -out=tfplan
terraform show tfplan
terraform apply tfplan
```

The saved plan file locks the exact diff—useful in CI where operators should not re-plan with different variables between steps.

## Operational commands (reference)

```bash
cd terraform/essentials/labs/lab03-plan-apply-destroy
terraform init
terraform plan
terraform apply
terraform show
terraform destroy

cd ../lab04-fmt-validate
terraform fmt
terraform validate
terraform plan
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 03: Plan, Apply, Destroy](../../labmanuals/lab03-plan-apply-destroy.md) | Full create and teardown cycle with outputs |
| [Lab 04: Format and Validate](../../labmanuals/lab04-fmt-validate.md) | `fmt`, `validate`, sensitive outputs |
