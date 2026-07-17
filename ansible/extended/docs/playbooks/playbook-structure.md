# Playbook Structure

Ansible playbooks are YAML files that describe **what** should happen on **which** hosts.

## Anatomy

```yaml
---
- name: Human-readable play name
  hosts: webservers
  become: true
  vars:
    package_name: nginx
  tasks:
    - name: Install package
      ansible.builtin.apt:
        name: "{{ package_name }}"
        state: present
```

| Key | Purpose |
|-----|---------|
| `hosts` | Inventory pattern (group, host, or `all`) |
| `become` | Privilege escalation (sudo) |
| `vars` | Play-scoped variables |
| `tasks` | Ordered list of modules to run |
| `handlers` | Tasks triggered by `notify` |

## FQCN modules

Always use fully qualified collection names:

- `ansible.builtin.apt` not `apt`
- `ansible.builtin.service` not `service`
- `ansible.builtin.template` not `template`

## Idempotency

A well-written playbook can run twice with no unintended changes. Modules report `changed` only when state differs.

## Validation

```bash
ansible-playbook --syntax-check playbooks/site.yml
ansible-playbook --check playbooks/site.yml
```

## Related labs

- [lab03 — Node.js playbook](../../labmanuals/lab03-nodejs-playbook.md)
- [lab08 — Roles project](../../labmanuals/lab08-roles-project.md)
