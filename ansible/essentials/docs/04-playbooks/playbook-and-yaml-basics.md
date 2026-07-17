# Playbooks and YAML Basics

## Overview

A **playbook** is a YAML file listing one or more **plays**. Each play targets a host pattern, optionally escalates privileges with `become`, and runs **tasks** in order. Playbooks are repeatable, reviewable, and suitable for production automation—unlike ad hoc commands.

YAML rules that matter for Ansible:

- Use spaces for indentation (not tabs).
- List items start with `-`.
- Key/value pairs use `key: value`.
- Strings with special characters can be quoted.

## Key concepts

| Section | Purpose |
|---------|---------|
| `hosts` | Which inventory pattern to target |
| `become` | Run tasks as root via sudo |
| `tasks` | Modules to execute |
| `handlers` | Tasks that run only when notified |
| `notify` | Triggers a handler after a task reports `changed` |

**Handlers** run at the end of the play, and only once per handler name even if notified multiple times—ideal for service restarts.

## Diagram

[Playbook execution and handlers](../html/playbook-handlers.html)

## Example

See `labs/playbooks/apache.yml`:

```yaml
---
- name: Install and configure Apache
  hosts: webservers
  become: true
  tasks:
    - name: Install apache2
      ansible.builtin.apt:
        name: apache2
        state: present
        update_cache: true

    - name: Enable mod_rewrite
      ansible.builtin.apache2_module:
        name: rewrite
        state: present
      notify: Restart apache2

  handlers:
    - name: Restart apache2
      ansible.builtin.service:
        name: apache2
        state: restarted
```

Run:

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/apache.yml
```

## Idempotency

Run the playbook twice. The second run should show `changed=0` for install tasks if nothing drifted—proof the playbook describes state, not blind command replay.

## Hands-on labs

- [lab04 — Apache playbook](../../labmanuals/lab04-playbook-apache-webserver.md)

## Next steps

- [Ansible variables](../05-variables/ansible-variables.md)
