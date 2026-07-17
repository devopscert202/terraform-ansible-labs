# Ansible Architecture

## Overview

Ansible uses a **control node** (your laptop or a jump box) to push configuration to **managed nodes** (target servers). Nothing needs to be installed on targets beyond Python and SSH access—there is no central Ansible “server” agent.

Communication is SSH (port **22** on Linux). The control node reads inventory (which hosts exist), playbooks (what to do), and optional encrypted secrets (Vault), then runs tasks in parallel across the inventory pattern you specify.

## Key concepts

| Term | Meaning |
|------|---------|
| Control node | Where you run `ansible` and `ansible-playbook` |
| Managed node | A server listed in inventory |
| Inventory | Host names, groups, and connection variables |
| Playbook | YAML file listing plays, tasks, handlers |
| Module | Unit of work (`apt`, `service`, `template`, …) |
| Role | Reusable bundle of tasks, handlers, templates |

**FQCN modules** — Use fully qualified collection names such as `ansible.builtin.apt` so playbooks stay explicit and portable.

## Diagram

[Ansible architecture — interactive](../html/ansible-architecture.html)

## Example inventory snippet

INI format (`inventory/hosts.ini`):

```ini
[webservers]
web1 ansible_host=10.0.1.10 ansible_user=ubuntu
```

YAML format (`inventory/hosts.yaml`) expresses the same hosts under `all.children`.

## Hands-on labs

- [lab01 — static inventory](../../labmanuals/lab01-inventory-static-hosts.md)
- [lab02 — hosts and groups](../../labmanuals/lab02-inventory-hosts-groups.md)

## Next steps

- [Inventory INI and YAML](../02-inventory/inventory-ini-and-yaml.md)
- [Ad hoc commands](../03-adhoc/adhoc-commands.md)
