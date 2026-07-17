# Ansible Roles

> **Curriculum:** Ansible Essentials · **Brand:** `#EE0000` · **Lab targets:** Ubuntu 22.04 · **SSH:** port 22

## Overview

A **role** packages tasks, handlers, defaults, templates, files, and metadata into a standard directory tree under `roles/<name>/`. Playbooks stay short—they list roles instead of repeating task blocks. Roles are how teams share reusable automation (web server, database client, monitoring agent) and publish to Ansible Galaxy.

The lab role `roles/webserver/` installs Apache, enables `mod_rewrite`, ensures the service runs, and restarts on configuration changes. Playbook `playbooks/role-site.yml` invokes it in three lines.

**Interactive reference:** [roles-and-vault.html](../../html/roles-and-vault.html)

---

## Key Concepts

### Standard Directory Layout

```
roles/webserver/
├── defaults/main.yml    # low-precedence variables (override-friendly)
├── tasks/main.yml       # main task list (required for most roles)
├── handlers/main.yml    # notified actions (restarts, reloads)
├── templates/           # Jinja2 templates (.j2)
├── files/               # static files (copy module)
├── vars/main.yml        # role variables (higher than defaults)
├── meta/main.yml        # dependencies, Galaxy metadata
└── README.md            # documentation (optional)
```

Ansible auto-loads `tasks/main.yml`, `handlers/main.yml`, and `defaults/main.yml` when the role is listed—no explicit import required.

### Role Invocation

```yaml
---
- name: Site with webserver role
  hosts: webservers
  become: true
  roles:
    - webserver
```

With parameters:

```yaml
roles:
  - role: webserver
    vars:
      web_package: apache2
```

### Execution Order (Multi-Role)

```
Play starts
  → Role A: all tasks
  → Role B: all tasks
  → Handlers (once, end of play)
Play ends
```

Extended lab `site.yml` uses `common` then `webserver` then `nodejs_app`.

---

## Lab Role: webserver

### defaults/main.yml

```yaml
---
web_package: apache2
web_service: apache2
```

Lowest precedence—consumers override without editing role code.

### tasks/main.yml

```yaml
---
- name: Install web package
  ansible.builtin.apt:
    name: "{{ web_package }}"
    state: present
    update_cache: true

- name: Enable mod_rewrite
  ansible.builtin.apache2_module:
    name: rewrite
    state: present
  notify: Restart web service

- name: Ensure web service running
  ansible.builtin.service:
    name: "{{ web_service }}"
    state: started
    enabled: true
```

### handlers/main.yml

```yaml
---
- name: Restart web service
  ansible.builtin.service:
    name: "{{ web_service }}"
    state: restarted
```

**Critical:** `notify: Restart web service` must match handler `name` exactly.

---

## ansible.cfg and roles_path

```ini
[defaults]
roles_path = roles
```

Playbooks run from `ansible/essentials/labs/` resolve `roles/webserver` relative to this path.

---

## ansible-galaxy init

Scaffold a new role:

```bash
ansible-galaxy init myrole
```

Creates full skeleton including `meta/main.yml`, `tests/`, and `README.md`. Lab role `webserver` is pre-built—do not overwrite when practicing.

### Install from Galaxy

```bash
ansible-galaxy install geerlingguy.apache
```

`requirements.yml`:

```yaml
---
roles:
  - name: geerlingguy.apache
    version: 3.1.0
```

```bash
ansible-galaxy install -r requirements.yml
```

---

## Role vs Inline Playbook

| Criterion | Inline (`apache.yml`) | Role (`webserver`) |
|-----------|----------------------|-------------------|
| Lines in playbook | Many tasks | `roles: [webserver]` |
| Reuse across projects | Copy/paste | Import role |
| Testing | Coupled to playbook | Molecule / targeted play |
| Galaxy publishing | No | Yes with `meta/main.yml` |
| Lab | Lab 04 | Lab 06 |

### When to Extract a Role

| Signal | Action |
|--------|--------|
| Same tasks in 2+ playbooks | Create role |
| Team owns "web tier" separately | Role + dedicated repo |
| Single lab exercise | Inline OK |
| Need dependency chain | `meta/main.yml` dependencies |

---

## Variable Precedence in Roles

```
extra vars (-e)
    ▼
play vars / vars_files
    ▼
inventory group_vars / host_vars
    ▼
role vars (vars/main.yml)
    ▼
role defaults (defaults/main.yml)
```

Override `web_package` in `group_vars/webservers.yml` without touching `roles/webserver/tasks/main.yml`.

---

## meta/main.yml (Dependencies)

Extended pattern:

```yaml
---
dependencies:
  - role: common
```

Ansible runs `common` role before dependent role automatically.

---

## Run the Lab Role

```bash
cd ansible/essentials/labs
ansible-playbook -i inventory/hosts.ini.local playbooks/role-site.yml --syntax-check
ansible-playbook -i inventory/hosts.ini.local playbooks/role-site.yml
ansible webservers -i inventory/hosts.ini.local -b \
  -m ansible.builtin.command -a "systemctl is-active apache2"
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `the role 'webserver' was not found` | Wrong cwd or roles_path | Run from `labs/`; check ansible.cfg |
| Handler never runs | notify name mismatch | Compare task notify to handler name |
| Wrong package installed | Overridden variable | Check group_vars and `-e` |
| Tasks run twice | Role listed twice | Deduplicate `roles:` list |
| Template not found in role | Path | Use `templates/foo.j2` without role prefix in task |
| Role changes ignored | Old playbook cache | N/A in Ansible; check correct role path |

### Handler Name Break-Fix Example

```yaml
# WRONG
notify: restart web service
# handler name: Restart web service  → no match

# RIGHT
notify: Restart web service
```

Extended [lab09 break-fix](../../extended/labmanuals/lab09-break-fix-drills.md) covers this scenario.

---

## Directory Roles vs collections

| Type | Path | Use |
|------|------|-----|
| Standalone role | `roles/webserver/` | Lab, simple projects |
| Collection role | `collections/namespace/name/roles/` | Enterprise, versioning |
| Galaxy role | `~/.ansible/roles/` | Third-party install |

Lab uses standalone directory roles.

---

## Hands-on Labs

| Lab | Topic | Manual |
|-----|-------|--------|
| Lab 06 | Create and run role | [lab06](../../labmanuals/lab06-roles-create.md) |
| Lab 07 | Vault + capstone | [lab07](../../labmanuals/lab07-vault-and-nodejs-capstone.md) |

Extended: [lab08 roles project](../../extended/labmanuals/lab08-roles-project.md)

**HTML companion:** [roles-and-vault.html](../../html/roles-and-vault.html)

---

## Production Practices

| Practice | Rationale |
|----------|-----------|
| One role per concern | webserver ≠ database |
| README per role | Document variables and examples |
| Pin Galaxy versions | Reproducible builds |
| Molecule tests | CI for roles |
| defaults over vars | Easier overrides |

---

## Next Steps

1. Complete [Lab 06](../../labmanuals/lab06-roles-create.md).
2. Protect secrets with [Ansible Vault](../07-vault/ansible-vault.md).
3. Explore multi-role `site.yml` in [Extended track](../../extended/labmanuals/lab08-roles-project.md).

---

## Quick Reference

```bash
find roles/webserver -type f
ansible-galaxy init myrole
ansible-playbook -i inventory/hosts.ini.local playbooks/role-site.yml
```

```yaml
roles:
  - webserver
```
