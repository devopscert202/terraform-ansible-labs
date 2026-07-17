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

## Hours 11–20: Terraform essentials

| Block | Time | Lab | Topic |
|-------|------|-----|-------|
| Intro | 30 min | docs | IaC, Terraform workflow |
| Providers | 1 h | lab01 | init, providers |
| Compute | 1.25 h | lab02 | EC2 + security group |
| Workflow | 1 h | lab03 | plan, apply, destroy |
| Quality | 30 min | lab04 | fmt, validate |
| Variables | 1.25 h | lab05 | vars, outputs, locals |
| State | 45 min | lab06 | Local state file |
| Modules | 1.25 h | lab07 | Reusable module |
| Secrets | 45 min | lab08 | tfvars, TF_VAR |
| Wrap-up | 45 min | — | destroy, review |

Path: [terraform/essentials/labmanuals/](../terraform/essentials/labmanuals/)

## After the bootcamp

Optional depth: [ansible/extended/](../ansible/extended/) then [terraform/extended/](../terraform/extended/).
