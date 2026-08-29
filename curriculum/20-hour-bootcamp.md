# 20-Hour Bootcamp Agenda

**10 hours Ansible** + **10 hours Terraform** — instructor-led, pre-provisioned AWS EC2 ([setup](setup/aws-lab-environment.md)).

## Hours 1–10: Ansible essentials

| Block | Time | Lab | Topic |
|-------|------|-----|-------|
| Intro | 30 min | docs | CM, IaC, Ansible architecture |
| Inventory | 1 h | lab01–02 | Static inventory, groups |
| Ad hoc | 45 min | lab03 | ping, shell, apt, service |
| Playbook | 1.25 h | lab04 | Apache, become, handlers |
| Variables | 45 min | lab05 | group_vars, templates |
| Roles | 1.25 h | lab06 | Role layout |
| Vault + capstone | 1.25 h | lab07 | Vault, Node.js project |
| Wrap-up | 45 min | — | Idempotency, cleanup |

Path: [ansible/essentials/labmanuals/](../ansible/essentials/labmanuals/)

## Hours 11–20: Terraform — Basic tier plus early Intermediate

The instructor-led window covers the **Basic tier in full (`lab00`–`lab05`)** and the **first three
Intermediate labs (`lab06`–`lab08`)**. Everything from `lab09` onward is self-paced.

| Block | Time | Lab | Topic |
|-------|------|-----|-------|
| Intro | 30 min | [AWS primer](../terraform/html/aws-primer.html) | Region, VPC, subnet, gateway, security group, EC2, IAM keys |
| Credentials | 45 min | lab00 | Access keys, environment variables, provider block, first `init` |
| Providers | 45 min | lab01 | `required_providers`, version constraints, lock file |
| Console vs code | 45 min | lab02 | Build a VPC by hand, then argue why that does not scale |
| Compute | 1.25 h | lab03 | AMI data source, security group, first EC2 instance |
| Workflow | 1 h | lab04 | `plan`, `apply`, `destroy`, saved plans |
| Quality | 30 min | lab05 | `fmt`, `validate`, sensitive outputs |
| Variables | 1.25 h | lab06 | Typed variables, locals, outputs |
| Secrets | 45 min | lab07 | tfvars, precedence, `sensitive`, `TF_VAR_` |
| State | 45 min | lab08 | `terraform.tfstate`, refresh, drift |
| Wrap-up | 45 min | — | `destroy` everything, key rotation, what comes next |

Path: [terraform/labmanuals/](../terraform/labmanuals/README.md) · Concepts:
[basic.html](../terraform/html/basic.html), [intermediate.html](../terraform/html/intermediate.html)

## After the bootcamp (self-paced)

| Assign | Labs | Why |
|--------|------|-----|
| Terraform Intermediate, remainder | `lab09`–`lab12` | Modules, collections, functions, dynamic blocks |
| Terraform Advanced | `lab13`–`lab21` | Multiple providers, provisioners, workspaces, S3 backend with locking, migration, remote state, capstone |
| Ansible extended | lab01–lab09 | Facts, loops, dynamic inventory, break-fix drills |

`lab21` is the capstone: VPC, internet gateway, route table, public subnet, security group, and an
EC2 instance that serves a page over HTTP. It is the intended end point of the Terraform track.
