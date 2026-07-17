# Terraform Essentials Lab Manuals

Eight concise, validation-first labs adapted from the supplied course materials. Each lab is self-contained under `../labs/` and targets Terraform 1.5+ with AWS provider `~> 5.0` where AWS is used.

| Lab | Focus | Source alignment |
|---|---|---|
| 01 | Providers and initialization | L8 AP-01 |
| 02 | EC2 instance | L7 AP-02 |
| 03 | Plan, apply, destroy | L8 AP-07 |
| 04 | Format and validate | L8 AP-05 |
| 05 | Variables and locals | L10 AP-02 |
| 06 | Local state | L9 AP-01 |
| 07 | Simple VPC module | L8 LEP (condensed) |
| 08 | tfvars, validation, and secrets | L10 AP-03 |

## Before you begin

Install Terraform 1.5 or later and authenticate AWS without putting credentials in code. For a named profile, run `export AWS_PROFILE=your-profile` and verify with `aws sts get-caller-identity`. On AWS compute, use an attached IAM role instead. Every AWS lab must be destroyed after use to avoid charges.

Run commands from the matching `labs/labNN-*` directory. Do not commit `.terraform/`, `.terraform.lock.hcl`, `terraform.tfstate*`, `*.tfvars`, or generated plans.
