# 06 — Variables, Locals, and Outputs

Input variables make a module configurable. Locals name derived or repeated values. Outputs expose selected results to users or calling modules.

Set values with a committed, non-secret `terraform.tfvars` only when appropriate; prefer environment-specific `*.tfvars` files excluded from source control. Mark sensitive inputs and outputs as `sensitive = true`, but remember that sensitive values can still reside in state.
