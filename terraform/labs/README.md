# Terraform Lab Code

Twenty-five directories, `lab00`–`lab24`, one **root module** each: a self-contained set of `.tf`
files with its own state. Run every command from inside the lab directory, never from this
parent — sibling directories must not share state.

```bash
cd terraform/labs/lab03-first-ec2
terraform init
terraform validate
terraform plan
terraform apply
terraform destroy      # when you are finished
```

Follow the matching manual in [`../labmanuals/`](../labmanuals/) rather than reading the code
cold. Full index: [`../labmanuals/README.md`](../labmanuals/README.md).

## Directories

A lab only carries the files it actually teaches — `variables.tf` appears where variables are the
subject, `backend.hcl.example` where remote state is.

| Lab | Directory | Files beyond `main.tf` |
|---|---|---|
| 00 | `lab00-aws-setup-and-init/` | — |
| 01 | `lab01-providers-init/` | — |
| 02 | `lab02-console-vpc/` | `README.md` only — this lab is built in the AWS console, so there is no `.tf` |
| 03 | `lab03-first-ec2/` | `variables.tf`, `outputs.tf`, `terraform.tfvars.example` |
| 04 | `lab04-plan-apply-destroy/` | — |
| 05 | `lab05-fmt-validate/` | — |
| 06 | `lab06-variables-outputs/` | `variables.tf`, `outputs.tf`, `terraform.tfvars.example` |
| 07 | `lab07-tfvars-secrets/` | `variables.tf`, `outputs.tf`, `terraform.tfvars.example` |
| 08 | `lab08-local-state/` | `outputs.tf` |
| 09 | `lab09-modules/` | `variables.tf`, `outputs.tf`, `terraform.tfvars.example`, `modules/` |
| 10 | `lab10-capstone-vpc-ec2/` | `variables.tf`, `outputs.tf`, `terraform.tfvars.example` |
| 11 | `lab11-collections/` | `variables.tf`, `outputs.tf` |
| 12 | `lab12-functions/` | `variables.tf`, `outputs.tf` |
| 13 | `lab13-multi-provider/` | `variables.tf`, `terraform.tfvars.example` |
| 14 | `lab14-local-exec-provisioner/` | — |
| 15 | `lab15-remote-exec-provisioner/` | `terraform.tfvars.example` |
| 16 | `lab16-workspaces/` | — |
| 17 | `lab17-s3-backend/` | `backend.hcl.example` |
| 18 | `lab18-state-keys-locking/` | `backend.hcl.example` |
| 19 | `lab19-state-migration/` | `backend.hcl.example` |
| 20 | `lab20-remote-state-consumer/` | `terraform.tfvars.example` |
| 21 | `lab21-dynamic-blocks/` | `variables.tf`, `outputs.tf` |
| 22 | `lab22-ec2-s3-backend/` | `variables.tf`, `outputs.tf`, `terraform.tfvars.example`, `backend.hcl.example` |
| 23 | `lab23-s3-bucket/` | `variables.tf`, `outputs.tf` |

## Conventions

| Rule | Detail |
|---|---|
| Terraform version | `required_version = ">= 1.5.0"` in every root module, except `lab17`–`lab19` and `lab22`, which need `>= 1.11.0` for `use_lockfile` |
| AWS provider | `version = "~> 5.0"` |
| Region | `us-east-2` |
| Instance type | `t3.micro` |
| AMI | Resolved with `data "aws_ami"` and `most_recent = true` — never a hardcoded ID |
| Variables | Every `variable` declares a `type` and a `description`; secrets add `sensitive = true` |
| Tags | Every AWS resource carries `Name` and `Lab = "labNN"` |
| Formatting | `terraform fmt -check` and `terraform validate` must pass |

## Never commit

`.terraform/`, `.terraform.lock.hcl`, `*.tfstate`, `*.tfstate.backup`, real `terraform.tfvars`,
real `backend.hcl`, or any private key. Copy the `.example` files locally and leave the copies
untracked. State files hold resource IDs and every value marked `sensitive`, in plain text.
