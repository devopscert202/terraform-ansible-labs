# Ansible Variables

> **Curriculum:** Ansible Essentials · **Brand:** `#EE0000` · **Lab targets:** Ubuntu 22.04 · **SSH:** port 22

## Overview

Variables make playbooks reusable across environments. Values come from inventory, `group_vars`/`host_vars`, play `vars`, role `defaults`, `vars_files`, registered task output, facts, and CLI extra vars (`-e`). **Jinja2** templates (`*.j2`) substitute variables into configuration files at deploy time.

In this track, `inventory/group_vars/webservers.yml` defines `webserver_port` and `app_env`, consumed by `templates/motd.j2` and `playbooks/vars-demo.yml`.

**Interactive reference:** [variables-templates.html](../../html/variables-templates.html)

---

## Key Concepts

| Source | Location | Precedence (low → high) |
|--------|----------|-------------------------|
| Role defaults | `roles/<role>/defaults/main.yml` | Lowest |
| Inventory group_vars | `inventory/group_vars/<group>.yml` | Low |
| Inventory host_vars | `inventory/host_vars/<host>.yml` | Medium |
| Play vars | `vars:` in playbook | Higher |
| vars_files | Encrypted or plain YAML | Higher |
| Task register / set_fact | Runtime | High |
| Extra vars `-e` | CLI | Highest |

Host-level variables override group-level for the same key.

### Variable Flow Diagram

```
inventory/group_vars/webservers.yml
        │
        ├── app_env: production
        └── webserver_port: 80
                │
                ▼
    playbooks/vars-demo.yml (template task)
                │
                ▼
    templates/motd.j2  ──render on control node──►  /etc/motd on targets
```

---

## group_vars in the Lab

File: `inventory/group_vars/webservers.yml`

```yaml
---
webserver_port: 80
app_env: production
```

| Variable | Value | Used by |
|----------|-------|---------|
| `webserver_port` | `80` | `motd.j2`, future conditionals |
| `app_env` | `production` | `motd.j2`, debug tasks |

Ansible auto-loads this file when a host belongs to group `webservers`—regardless of INI or YAML inventory format.

```bash
ansible-inventory -i inventory/hosts.ini.local --host web1 | grep app_env
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.debug -a "var=app_env"
```

---

## Jinja2 Templates

File: `templates/motd.j2`

```jinja2
Welcome to {{ inventory_hostname }}
Environment: {{ app_env }}
Web port: {{ webserver_port }}
```

| Syntax | Purpose | Example |
|--------|---------|---------|
| `{{ var }}` | Substitute value | `{{ app_env }}` |
| `{% if %}` | Conditional block | `{% if app_env == 'production' %}` |
| `{% for %}` | Loop | `{% for h in groups['webservers'] %}` |
| `\| filter` | Transform value | `{{ name \| upper }}` |
| `\| default()` | Fallback | `{{ missing \| default('n/a') }}` |

### Magic Variables (Common)

| Variable | Meaning |
|----------|---------|
| `inventory_hostname` | Inventory alias (`web1`) |
| `ansible_host` | Connection IP |
| `groups` | Dict of group → host lists |
| `group_names` | Groups current host belongs to |
| `hostvars` | All host variables |

---

## template Module

Playbook: `playbooks/vars-demo.yml`

```yaml
---
- name: Deploy MOTD from template
  hosts: webservers
  become: true
  tasks:
    - name: Template motd
      ansible.builtin.template:
        src: ../templates/motd.j2
        dest: /etc/motd
        mode: "0644"
```

| Parameter | Purpose |
|-----------|---------|
| `src` | Template path (relative to playbook) |
| `dest` | Target file path |
| `mode` | File permissions |
| `owner` / `group` | Optional ownership |
| `backup` | Keep `.bak` on change |

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/vars-demo.yml
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.command -a "cat /etc/motd"
```

Rendering happens on the **control node**; only the result is copied to targets.

---

## Overriding Variables

### CLI extra vars (highest precedence)

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/vars-demo.yml -e "app_env=staging"
```

### Play vars

```yaml
- name: Deploy with override
  hosts: webservers
  vars:
    app_env: staging
  tasks:
    - ansible.builtin.template: ...
```

### Role parameter

```yaml
roles:
  - role: webserver
    vars:
      web_package: apache2
```

---

## Role Defaults vs group_vars

`roles/webserver/defaults/main.yml`:

```yaml
---
web_package: apache2
web_service: apache2
```

| Layer | Who sets it | Example |
|-------|-------------|---------|
| Role defaults | Role author | `web_package` |
| group_vars | Environment owner | `app_env` |
| Extra vars | Operator / CI | `-e app_env=staging` |

**Rule:** Put override-friendly values in role `defaults`; put environment-specific values in inventory `group_vars`.

---

## vars_files and Vault

```yaml
vars_files:
  - ../vault/secrets.yml
```

Encrypted vault files decrypt at load time when vault password is supplied. Variables like `api_token` become available to tasks and templates.

See [Ansible Vault](../07-vault/ansible-vault.md) and lab 07.

---

## Debugging Variables

```bash
# Merged host variables
ansible-inventory --host web1

# Single variable
ansible web1 -m ansible.builtin.debug -a "var=app_env"

# All facts
ansible web1 -m ansible.builtin.setup

# Filtered facts
ansible web1 -m ansible.builtin.setup -a "filter=ansible_distribution*"
```

In playbooks:

```yaml
- ansible.builtin.debug:
    var: app_env
- ansible.builtin.debug:
    msg: "Port is {{ webserver_port }}"
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `undefined variable` | Host not in group / typo | Check group_vars filename matches group |
| Template not found | Wrong `src` path | Relative to playbook directory |
| Old value on disk | Cached? / wrong override | Check `-e`; re-run template task |
| Jinja syntax error | Unclosed `{{` | Validate template locally |
| `changed` every run | Non-deterministic template | Remove timestamps from template |
| group_vars ignored | File naming | Must be `group_vars/webservers.yml` |
| Vault var undefined | Missing password | `--vault-password-file` |

### Variable Precedence Pitfall

```bash
# group_vars says production, but -e wins:
ansible-playbook vars-demo.yml -e "app_env=staging"
# MOTD shows staging
```

---

## Multi-Environment Pattern (Reference)

```
inventories/
├── production/
│   ├── hosts.ini
│   └── group_vars/webservers.yml   # app_env: production
└── staging/
    ├── hosts.ini
    └── group_vars/webservers.yml   # app_env: staging
```

```bash
ansible-playbook -i inventories/staging/hosts.ini playbooks/vars-demo.yml
```

Same playbook, different variable files.

---

## Hands-on Labs

| Lab | Topic | Manual |
|-----|-------|--------|
| Lab 02 | group_vars intro | [lab02](../../labmanuals/lab02-inventory-hosts-groups.md) |
| Lab 05 | Templates | [lab05](../../labmanuals/lab05-playbook-variables.md) |
| Lab 07 | Vault vars | [lab07](../../labmanuals/lab07-vault-and-nodejs-capstone.md) |

**HTML companion:** [variables-templates.html](../../html/variables-templates.html)

---

## Best Practices

| Practice | Rationale |
|----------|-----------|
| No secrets in group_vars plaintext | Use Vault |
| Descriptive variable names | `webserver_port` not `p` |
| Defaults in roles, env in inventory | Clear ownership |
| Quote Jinja in YAML when ambiguous | Avoid parse errors |
| Use `default` filter for optional keys | Safer templates |

---

## Next Steps

1. Complete [Lab 05](../../labmanuals/lab05-playbook-variables.md).
2. Package logic in [Ansible Roles](../06-roles/ansible-roles.md).
3. Encrypt secrets in [Ansible Vault](../07-vault/ansible-vault.md).

---

## Quick Reference

```yaml
# group_vars/webservers.yml
app_env: production
webserver_port: 80

# template
Environment: {{ app_env }}

# run
ansible-playbook -i inventory/hosts.ini.local playbooks/vars-demo.yml -e "app_env=staging"
```
