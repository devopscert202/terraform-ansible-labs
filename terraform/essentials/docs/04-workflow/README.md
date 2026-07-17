# 04 — Terraform Workflow

The core workflow is `init`, `fmt`, `validate`, `plan`, `apply`, then `destroy`. `validate` checks configuration structure; it does not prove cloud permissions or that an apply will succeed.

Prefer saved plans for controlled changes: `terraform plan -out=tfplan` followed by `terraform apply tfplan`. Do not reuse a saved plan after the configuration or environment changes.
