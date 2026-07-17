# Ad Hoc Commands

## Overview

Ad hoc commands run a **single module** against a host pattern **without** writing a playbook. They are ideal for quick checks (`ping`, `uptime`), one-off fixes, and exploring facts before you codify tasks in a playbook.

Syntax:

```bash
ansible <host-pattern> -i <inventory> -m <module> -a "<arguments>"
```

Add `-b` when the module needs root (for example `apt` on Ubuntu).

## Key concepts

| Use case | Module | Example |
|----------|--------|---------|
| Connectivity | `ansible.builtin.ping` | `ansible all -m ansible.builtin.ping` |
| Run command | `ansible.builtin.command` | `ansible web1 -m ansible.builtin.command -a "uptime"` |
| Package (Ubuntu) | `ansible.builtin.apt` | `ansible web1 -b -m ansible.builtin.apt -a "name=tree state=present"` |
| Service | `ansible.builtin.service` | `ansible webservers -b -m ansible.builtin.service -a "name=apache2 state=started"` |
| Facts | `ansible.builtin.setup` | `ansible web1 -m ansible.builtin.setup -a "filter=ansible_distribution*"` |

On Ubuntu targets, prefer `apt` over `yum` examples you may see in generic training slides.

## Diagram

[Ad hoc vs playbook](../html/adhoc-vs-playbook.html)

## Example session

```bash
cd ~/terraform-ansible-labs/ansible/essentials/labs
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.ping
ansible web1 -i inventory/hosts.ini.local -b -m ansible.builtin.apt \
  -a "name=tree state=present update_cache=yes"
```

## Hands-on labs

- [lab03 — ad hoc commands](../../labmanuals/lab03-adhoc-commands.md)

## Next steps

- [Playbook and YAML basics](../04-playbooks/playbook-and-yaml-basics.md)
