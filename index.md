---
layout: default
title: Home
---

# Terraform & Ansible Labs

Configuration management and infrastructure as code — concise labs, concept docs, and interactive HTML.

**Live site:** [devopscert202.github.io/terraform-ansible-labs](https://devopscert202.github.io/terraform-ansible-labs/)

## Interactive HTML catalogs

Open these in your browser (offline-capable, embedded CSS):

| Track | Catalog |
|-------|---------|
| Ansible essentials | [ansible/essentials/html/index.html](ansible/essentials/html/index.html) |
| Ansible extended | [ansible/extended/html/index.html](ansible/extended/html/index.html) |
| Terraform track (22 labs) | [terraform/html/index.html](terraform/html/index.html) |
| Terraform 101 — read first | [terraform/html/terraform-101.html](terraform/html/terraform-101.html) |
| Terraform AWS primer — read second | [terraform/html/aws-primer.html](terraform/html/aws-primer.html) |
| Terraform Basic concepts | [terraform/html/basic.html](terraform/html/basic.html) |
| Terraform Intermediate concepts | [terraform/html/intermediate.html](terraform/html/intermediate.html) |
| Terraform Advanced concepts | [terraform/html/advanced.html](terraform/html/advanced.html) |

## Lab manuals & curriculum

- [20-hour bootcamp](curriculum/20-hour-bootcamp.md)
- [Day-wise LVC agenda](curriculum/day-wise-agenda.md)
- [Learning paths](curriculum/learning-paths.md)
- [AWS lab setup](curriculum/setup/aws-lab-environment.md)
- [Ansible essentials labs](ansible/essentials/labmanuals/)
- [Ansible extended labs](ansible/extended/labmanuals/)
- [Terraform track](terraform/README.md) — [lab index, all 22](terraform/labmanuals/README.md)

## Learning paths

1. **Ansible** (10 h) — inventory, playbooks, roles, vault
2. **Terraform Basic** (`lab00`–`lab05`) — credentials, providers, first EC2, the core workflow, quality gates
3. **Terraform Intermediate** (`lab06`–`lab12`) — variables, secrets, state, modules, collections, functions, dynamic blocks
4. **Terraform Advanced** (`lab13`–`lab21`) — multiple providers, provisioners, workspaces, remote state, capstone
5. **Ansible extended** — facts, loops, dynamic inventory, break-fix drills

New to Terraform? Read the two primers before lab00, in this order:

1. **[Terraform 101](terraform/html/terraform-101.html)** — what Terraform is, HCL, providers, version constraints, the CLI, state, drift
2. **[AWS Primer](terraform/html/aws-primer.html)** — region, VPC, CIDR, subnet, internet gateway, route table, security group, EC2, IAM access keys
