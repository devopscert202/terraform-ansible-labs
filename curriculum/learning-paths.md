# Learning Paths

## 1. 20-Hour Bootcamp (recommended)

1. [AWS lab setup](setup/aws-lab-environment.md)
2. [Ansible essentials](../ansible/essentials/labmanuals/) — lab01 → lab07
3. [Terraform AWS primer](../terraform/html/aws-primer.html) — read before touching AWS
4. [Terraform](../terraform/labmanuals/README.md) — `lab00` → `lab08` (Basic tier in full, plus the
   first three Intermediate labs)

Agenda: [20-hour-bootcamp.md](20-hour-bootcamp.md)

## 2. Terraform, self-paced remainder

Finish the bootcamp window first, then continue in order:

| Tier | Labs | Topics |
|---|---|---|
| Intermediate, remainder | `lab09` → `lab12` | Modules, `for_each` over collections, built-in functions, dynamic blocks |
| Advanced | `lab13` → `lab21` | Multiple providers, `local-exec` and `remote-exec`, workspaces, S3 backend, state keys and locking, migration, remote state consumers, capstone |

Index: [terraform/labmanuals/README.md](../terraform/labmanuals/README.md) · Concepts:
[intermediate.html](../terraform/html/intermediate.html),
[advanced.html](../terraform/html/advanced.html)

## 3. Terraform, full track end to end

If you are not on the bootcamp clock, just run `lab00` → `lab21` in order. Each lab assumes the one
before it. Total: **22 labs in three tiers** — Basic `lab00`–`lab05`, Intermediate `lab06`–`lab12`,
Advanced `lab13`–`lab21`.

## 4. Ansible extended

Complete Ansible essentials first, then [ansible/extended/labmanuals/](../ansible/extended/labmanuals/) lab01 → lab09.

## 5. Full LVC reference

Original 4-day vendor agenda (reference only): [day-wise-agenda.md](day-wise-agenda.md)
