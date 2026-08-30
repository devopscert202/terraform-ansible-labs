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
| Compute | 1.25 h | lab03 | AMI data source, own VPC and subnets, security group, first EC2 instance |
| Workflow | 1 h | lab04 | `plan`, `apply`, `destroy`, saved plans |
| Quality | 30 min | lab05 | `fmt`, `validate`, sensitive outputs |
| Variables | 1.5 h | lab06 | Typed variables, every variable type, locals, outputs |
| Secrets | 45 min | lab07 | tfvars, precedence, `sensitive`, `TF_VAR_` |
| State | 45 min | lab08 | `terraform.tfstate`, refresh, drift |
| Wrap-up | 45 min | — | `destroy` everything, key rotation, what comes next |
| Breaks and Q&A | 45 min | — | Distributed across the block, not taken in one piece |

Total 10 h. `lab06` carries the largest single block because it now walks every variable type.
Path: [terraform/labmanuals/](../terraform/labmanuals/README.md) · Concepts:
[concepts.html](../terraform/html/concepts.html) — the window's topics run from
[`lab00`](../terraform/html/concepts.html#lab00-foundations) to
[`lab08`](../terraform/html/concepts.html#lab08-local-state) on that page

## After the bootcamp (self-paced)

The track is **25 labs, `lab00`–`lab24`**. The bootcamp window covers nine of them; the remaining
fifteen are self-paced, in order.

| Assign | Labs | Est. time | Why |
|--------|------|-----------|-----|
| Terraform Intermediate, remainder | `lab09`–`lab12` | ~4 h | Modules, the end-to-end capstone at `lab10`, collections, functions |
| Terraform Advanced, part 1 | `lab13`–`lab16` | ~4 h | Multiple providers, both provisioners, workspaces |
| Terraform Advanced, part 2 | `lab17`–`lab20` | ~4 h | S3 backend, state keys and locking, migration, remote state consumers |
| Terraform Advanced, part 3 | `lab21`–`lab24` | ~4 h | Dynamic blocks, the capstone rebuilt on a remote backend, an S3 bucket as a managed resource, `count` versus `for_each` |
| Ansible extended | lab01–lab09 | self-paced | Facts, loops, dynamic inventory, break-fix drills |

`lab10` is the capstone: VPC, internet gateway, route table, public subnet, security group, and an
EC2 instance that serves a page over HTTP. It sits mid-track deliberately, so a learner assembles a
working system before meeting the Advanced tooling — and it is the first lab whose instance is
reachable from outside, since `lab03` and `lab06` build networks with no internet gateway on
purpose. `lab22` builds the same topology again with its state in S3, `lab23` manages an S3 bucket
as an ordinary resource, and `lab24` closes the track on `count` versus `for_each`.
