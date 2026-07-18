# Terraform Quality: Format, Validate, and Review

## Objective (conceptual)

Quality gates catch mistakes **before** `apply` touches production. `terraform fmt` enforces consistent HCL so diffs stay readable in code review. `terraform validate` checks that blocks, references, and types are internally consistent—without calling cloud APIs. Together they form the minimum bar every commit should pass.

The mental model: **fmt** is style; **validate** is grammar; **plan** is semantics against live infrastructure. CI pipelines typically run all three on every pull request, then run `plan` with read-only credentials.

**Interactive reference:** [Core Workflow](../../html/workflow.html)

## terraform fmt

- Rewrites `.tf`, `.tfvars`, and `.tftest.hcl` files in place.
- `terraform fmt -check` exits non-zero in CI when files need formatting.
- Lab 04 starts with misaligned braces—`fmt` fixes them in one pass.

## terraform validate

- Requires `init` first (providers must be installed).
- Catches unknown arguments, wrong types, and broken references.
- Does **not** verify credentials, quotas, or that an AMI exists in your account.

## Sensitive outputs (Lab 04)

```hcl
output "formatted_example" {
  value     = random_string.formatted_example.result
  sensitive = true
}
```

- CLI masks the value in `apply` output and `terraform output`.
- Value remains in state—protect state files accordingly.
- Use for tokens, connection strings, or generated secrets in training scenarios.

## Pre-apply review checklist

- [ ] `terraform fmt -recursive` (from repo root or lab folder)
- [ ] `terraform validate`
- [ ] `terraform plan` reviewed line by line
- [ ] Destroy plan understood for any `forces replacement`
- [ ] Tags and names match environment policy

## Lab 04 configuration excerpt

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
```

After `fmt`, indentation and brace placement match HashiCorp style—easier for teammates and linters.

## Integrating with CI (concept)

Typical job steps:

1. `terraform init -backend=false` (validation-only jobs)
2. `terraform fmt -check`
3. `terraform validate`
4. `terraform plan` (with remote backend and credentials in CI secrets)

Extended track Lab 02 (`lab02-validate-only`) explores validate-only roots without apply.

## Common validate errors

| Message | Cause | Fix |
|---------|-------|-----|
| Missing required provider | Skipped `init` | Run `terraform init` |
| Reference to undeclared resource | Typo in address | Match `resource` block name |
| Invalid value for variable | Wrong type in tfvars | Align with `variable` block `type` |

## fmt in team workflows

Run `terraform fmt -recursive` from the essentials `labs/` parent before opening a PR if you touched multiple directories. Consistent formatting lets reviewers focus on logic—CIDR changes and security group rules—not brace placement.

Pair fmt with editor integration: the Terraform VS Code extension can format on save using the same rules as the CLI.

## validate vs plan

| Stage | Contacts cloud API? | Catches |
|-------|---------------------|---------|
| `validate` | No | Syntax, unknown args, type errors |
| `plan` | Yes (refresh) | Drift, quota errors, missing AMIs |

A green `validate` does not guarantee a green `plan`. Always run both before apply in AWS labs.

## Operational commands (reference)

```bash
cd terraform/essentials/labs/lab04-fmt-validate
terraform init
terraform fmt
terraform fmt -check -diff
terraform validate
terraform plan
terraform output -json   # structured output for scripts
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 04: Format and Validate](../../labmanuals/lab04-fmt-validate.md) | Fix formatting, validate config, sensitive output behavior |
| [Extended Lab 02: Validate Only](../../../extended/labmanuals/lab02-validate-only.md) | CI-style validate without apply |
