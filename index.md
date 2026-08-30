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
| Terraform track (25 labs) | [terraform/html/index.html](terraform/html/index.html) |
| Terraform 101 — read first | [terraform/html/terraform-101.html](terraform/html/terraform-101.html) |
| Terraform AWS primer — read second | [terraform/html/aws-primer.html](terraform/html/aws-primer.html) |
| Terraform concepts — all 26 topics, `lab00`–`lab24` on one page | [terraform/html/concepts.html](terraform/html/concepts.html) |

## Lab manuals & curriculum

- [20-hour bootcamp](curriculum/20-hour-bootcamp.md)
- [Day-wise LVC agenda](curriculum/day-wise-agenda.md)
- [Learning paths](curriculum/learning-paths.md)
- [AWS lab setup](curriculum/setup/aws-lab-environment.md)
- [Ansible essentials labs](ansible/essentials/labmanuals/)
- [Ansible extended labs](ansible/extended/labmanuals/)
- [Terraform track](terraform/README.md) — [lab index, all 25](terraform/labmanuals/README.md)

## Learning paths

1. **Ansible** (10 h) — inventory, playbooks, roles, vault
2. **Terraform** (`lab00`–`lab24`, 25 labs in one sequence) — credentials and providers, first EC2 in
   its own VPC, the core workflow, quality gates, variables and secrets, state, modules, the
   capstone public web server at `lab10`, collections and functions, multiple providers,
   provisioners, workspaces, remote state in S3 with locking, migration, dynamic blocks, the
   capstone rebuilt on a remote backend, S3 buckets, `count` vs `for_each`
3. **Ansible extended** — facts, loops, dynamic inventory, break-fix drills

Tier is a per-lab difficulty label, not a separate path: Basic `lab00`–`lab05` (6), Intermediate
`lab06`–`lab12` (7), Advanced `lab13`–`lab24` (12). Run the labs in numeric order.

New to Terraform? Read the two primers before lab00, in this order:

1. **[Terraform 101](terraform/html/terraform-101.html)** — what Terraform is, HCL, providers, version constraints, the CLI, state, drift
2. **[AWS Primer](terraform/html/aws-primer.html)** — region, VPC, CIDR, subnet, internet gateway, route table, security group, EC2, IAM access keys

Then keep **[concepts.html](terraform/html/concepts.html)** open alongside the labs: every topic in
lab order, each with a worked example and a line-by-line explanation.
