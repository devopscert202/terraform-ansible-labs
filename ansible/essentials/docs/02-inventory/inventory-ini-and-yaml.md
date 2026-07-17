# Inventory: INI and YAML

## Overview

Inventory tells Ansible **which machines to touch** and **how to connect**. Essentials labs use a **static** inventory file you edit by hand. Each host can belong to one or more groups; variables can be attached to hosts or groups.

Group names must be consistent everywhere—use `webservers`, not typos like `dbbservers` from older training material.

## Key concepts

- **Host pattern** — `web1`, `webservers`, `all`, or combinations used on the CLI and in `hosts:`.
- **Connection variables** — `ansible_host`, `ansible_user`, `ansible_python_interpreter`.
- **Group variables** — Stored in `inventory/group_vars/<groupname>.yml` (YAML syntax).
- **Formats** — INI (`hosts.ini`) or YAML (`hosts.yaml`); pick one style per project.

## Diagram

[Inventory and group_vars flow](../html/inventory-flow.html)

## Examples

INI:

```ini
[webservers]
web1 ansible_host=10.0.1.10 ansible_user=ubuntu

[webservers:vars]
ansible_python_interpreter=/usr/bin/python3
```

YAML:

```yaml
all:
  children:
    webservers:
      hosts:
        web1:
          ansible_host: 10.0.1.10
          ansible_user: ubuntu
```

Group variable file (`inventory/group_vars/webservers.yml`):

```yaml
webserver_port: 80
app_env: production
```

## Hands-on labs

- [lab01 — static inventory](../../labmanuals/lab01-inventory-static-hosts.md)
- [lab02 — hosts and groups](../../labmanuals/lab02-inventory-hosts-groups.md)

## Next steps

- [Ad hoc commands](../03-adhoc/adhoc-commands.md)
