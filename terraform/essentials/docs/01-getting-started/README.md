# 01 — Getting Started

Terraform describes desired infrastructure in `.tf` files, calculates a dependency graph, and records managed objects in state. Keep each lab isolated so its state and lifecycle are clear.

Use Terraform 1.5+ and AWS provider `~> 5.0`. Authenticate through the standard AWS credential chain: `AWS_PROFILE`, environment credentials supplied by the runtime, or an IAM role. Never add `access_key` or `secret_key` to a provider block.

```sh
terraform version
export AWS_PROFILE=training
aws sts get-caller-identity
```
