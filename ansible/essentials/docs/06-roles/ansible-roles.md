# Ansible Roles

## Overview

A **role** packages tasks, handlers, defaults, templates, and files into a standard directory tree. Playbooks stay short—they list roles instead of repeating task blocks. Roles are how teams share reusable automation (web server, database client, monitoring agent).

## Key concepts

Standard directories (use what you need):

```
roles/webserver/
├── defaults/main.yml    # low-precedence variables
├── tasks/main.yml       # required for most roles
├── handlers/main.yml    # notified actions
├── templates/           # Jinja templates
├── files/               # static files
└── meta/main.yml        # role metadata (optional)
```

Invoke a role from a playbook:

```yaml
---
- name: Site with webserver role
  hosts: webservers
  become: true
  roles:
    - webserver
```

Create a skeleton with `ansible-galaxy init webserver` (already provided in `labs/roles/webserver/`).

## Diagram

[Roles and Vault overview](../html/roles-and-vault.html)

## Example

`roles/webserver/defaults/main.yml` sets `web_package: apache2`. Tasks install the package, enable modules, and ensure the service is running. Handlers restart the service when configuration changes.

## Hands-on labs

- [lab06 — create and run a role](../../labmanuals/lab06-roles-create.md)

## Next steps

- [Ansible Vault](../07-vault/ansible-vault.md)
