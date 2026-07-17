# Ansible Variables

## Overview

Variables make playbooks reusable across environments. Values come from inventory, group/host var files, play `vars`, role `defaults`, and extra vars on the command line. **Jinja2** templates (`*.j2`) substitute variables into config files at deploy time.

In this track, group variables for `webservers` live in `inventory/group_vars/webservers.yml`.

## Key concepts

| Source | Typical location | Precedence |
|--------|------------------|------------|
| Role defaults | `roles/<role>/defaults/main.yml` | Lower |
| Inventory group_vars | `inventory/group_vars/<group>.yml` | Medium |
| Play vars / `vars_files` | In playbook | Higher |
| Extra vars `-e` | CLI | Highest |

**Templates** — The `ansible.builtin.template` module renders `templates/*.j2` on the control node and copies the result to targets.

## Diagram

[Variables and templates](../html/variables-templates.html)

## Example

`inventory/group_vars/webservers.yml`:

```yaml
webserver_port: 80
app_env: production
```

`templates/motd.j2`:

```jinja2
Welcome to {{ inventory_hostname }}
Environment: {{ app_env }}
Web port: {{ webserver_port }}
```

Playbook `playbooks/vars-demo.yml` deploys the template to `/etc/motd`.

## Hands-on labs

- [lab05 — variables and templates](../../labmanuals/lab05-playbook-variables.md)

## Next steps

- [Ansible roles](../06-roles/ansible-roles.md)
