# 08 — Modules

A module is a reusable directory of Terraform configuration. The root module calls it with `module` blocks and consumes declared outputs. Keep provider configuration in the root module and give child modules typed inputs and focused outputs.

The module lab creates a VPC and subnet. It is intentionally small; production network modules also need multi-AZ design, routing, security controls, and organizational tagging.
