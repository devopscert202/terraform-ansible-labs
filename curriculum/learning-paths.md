# Learning Paths

The Terraform track is **25 labs, `lab00`–`lab24`**, run in numeric order. Tier is a per-lab
difficulty label rather than a separate path: Basic `lab00`–`lab05` (6), Intermediate
`lab06`–`lab12` (7), Advanced `lab13`–`lab24` (12). All concept material for every lab lives on one
page, [terraform/html/concepts.html](../terraform/html/concepts.html).

## 1. 20-Hour Bootcamp (recommended)

1. [AWS lab setup](setup/aws-lab-environment.md)
2. [Ansible essentials](../ansible/essentials/labmanuals/) — lab01 → lab07
3. [Terraform 101](../terraform/html/terraform-101.html) then the
   [AWS primer](../terraform/html/aws-primer.html) — both before touching AWS
4. [Terraform](../terraform/labmanuals/README.md) — `lab00` → `lab08` (Basic tier in full, plus the
   first three Intermediate labs)

Agenda: [20-hour-bootcamp.md](20-hour-bootcamp.md)

## 2. Terraform, self-paced remainder

Finish the bootcamp window first, then continue in order:

| Labs | Tier label | Topics |
|---|---|---|
| `lab09` → `lab12` | Intermediate | Modules, the end-to-end capstone at `lab10`, `for_each` over collections, built-in functions |
| `lab13` → `lab24` | Advanced | Multiple providers, `local-exec` and `remote-exec`, workspaces, S3 backend, state keys and locking, migration, remote state consumers, dynamic blocks, the capstone rebuilt on a remote backend, an S3 bucket as a managed resource, and `count` versus `for_each` |

Index: [terraform/labmanuals/README.md](../terraform/labmanuals/README.md) · Concepts:
[concepts.html](../terraform/html/concepts.html) — jump to
[`lab09`](../terraform/html/concepts.html#lab09-modules) or
[`lab13`](../terraform/html/concepts.html#lab13-multi-provider)

## 3. Terraform, full track end to end

If you are not on the bootcamp clock, just run `lab00` → `lab24` in order. Each lab assumes the one
before it. Two milestones are worth planning around: `lab10` is the capstone, where a working public
web server appears mid-track, and `lab22` rebuilds that same topology with its state in S3 once
remote backends are familiar. `lab24` closes the track on `count` versus `for_each`.

## 4. Ansible extended

Complete Ansible essentials first, then [ansible/extended/labmanuals/](../ansible/extended/labmanuals/) lab01 → lab09.

## 5. Full LVC reference

Original 4-day vendor agenda (reference only): [day-wise-agenda.md](day-wise-agenda.md)
