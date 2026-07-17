# 05 — Formatting and Validation

`terraform fmt` normalizes HCL style. Use `terraform fmt -check -recursive` in CI to fail when formatting is needed. `terraform validate` requires initialized modules and providers and catches configuration-level errors.

Run both before a plan. They are fast feedback, not a substitute for reviewing a plan.
