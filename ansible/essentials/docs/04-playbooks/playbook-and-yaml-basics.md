# Playbooks and YAML Basics

> **Curriculum:** Ansible Essentials · **Brand:** `#EE0000` · **Lab targets:** Ubuntu 22.04 · **SSH:** port 22

## Overview

A **playbook** is a YAML file listing one or more **plays**. Each play targets a host pattern, optionally escalates privileges with `become`, and runs **tasks** in order. Playbooks are repeatable, reviewable in Git, and suitable for production—unlike ad hoc commands that live only in shell history.

The lab playbook `playbooks/apache.yml` installs Apache, enables `mod_rewrite`, and restarts the service via a **handler** only when configuration changes.

**Interactive reference:** [playbook-handlers.html](../../html/playbook-handlers.html)

---

## Key Concepts

| Section | Purpose | Lab example |
|---------|---------|-------------|
| `name` (play) | Human-readable play description | `Install and configure Apache` |
| `hosts` | Inventory pattern | `webservers` |
| `become` | Run tasks as root via sudo | `true` |
| `tasks` | Ordered list of modules | `apt`, `apache2_module` |
| `handlers` | Tasks run on notify at play end | `Restart apache2` |
| `notify` | Link task to handler by name | `notify: Restart apache2` |

### YAML Rules for Ansible

| Rule | Correct | Wrong |
|------|---------|-------|
| Indentation | 2 spaces | Tabs |
| Lists | `- item` | Missing dash |
| Key/value | `key: value` | `key=value` (except in `-a` strings) |
| Strings | `mode: "0644"` | Unquoted special chars |
| Document start | `---` optional but common | |

### Playbook Structure Diagram

```
playbooks/apache.yml
│
└── Play (list item)
    ├── name: Install and configure Apache
    ├── hosts: webservers
    ├── become: true
    ├── tasks:          ← executed in order
    │   ├── Install apache2
    │   └── Enable mod_rewrite (notify)
    └── handlers:       ← run once at end if notified
        └── Restart apache2
```

---

## Handlers and notify

Handlers solve a common problem: **restart a service only when config changes**, not on every playbook run.

| Behavior | Detail |
|----------|--------|
| Trigger | Task reports `changed` and has `notify: Handler name` |
| Timing | After all tasks in the play complete |
| Frequency | Once per handler name per play, even if notified multiple times |
| Name match | `notify` string must equal handler `name` exactly |

```
Task (changed) ──notify──► Handler queued
Task (ok)      ──no notify──► Handler skipped
         ... all tasks ...
End of play ──► Run queued handlers once
```

Common break-fix mistake: `notify: restart apache` vs handler `name: Restart apache2`—handler never runs.

---

## Lab Playbook Walkthrough

File: `labs/playbooks/apache.yml`

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

### Run Commands

```bash
cd ansible/essentials/labs
ansible-playbook -i inventory/hosts.ini.local playbooks/apache.yml --syntax-check
ansible-playbook -i inventory/hosts.ini.local playbooks/apache.yml
ansible-playbook -i inventory/hosts.ini.local playbooks/apache.yml  # second run: idempotent
```

---

## Idempotency

| Run | apt task | module task | Handler |
|-----|----------|-------------|---------|
| First | `changed` | `changed` | may run |
| Second | `ok` | `ok` | skipped |

Idempotency means **safe to re-run** anytime—configuration management converges to desired state without unnecessary side effects.

Modules like `ansible.builtin.apt` with `state: present` check current state before acting. `ansible.builtin.command` is **not** inherently idempotent—prefer dedicated modules.

---

## ansible-playbook CLI

| Flag | Purpose |
|------|---------|
| `-i inventory/path` | Override default inventory |
| `--syntax-check` | Validate YAML without executing |
| `--check` | Dry run (predict changes) |
| `--diff` | Show file diffs |
| `--limit web1` | Subset of hosts |
| `-v` to `-vvvv` | Verbosity |
| `--list-hosts` | Show targets only |
| `--list-tasks` | Show task order |
| `-e "key=val"` | Extra variables |

```bash
ansible-playbook playbooks/apache.yml -i inventory/hosts.ini.local --list-hosts
ansible-playbook playbooks/apache.yml -i inventory/hosts.ini.local --check --diff
```

---

## Play vs Task vs Module

```
Playbook
  └── Play (targets webservers, become true)
        └── Task: "Install apache2"
              └── Module: ansible.builtin.apt
                    └── args: name, state, update_cache
```

One playbook can contain multiple plays—for example web tier then db tier—in sequence.

---

## FQCN Modules in Playbooks

Always prefer fully qualified collection names:

```yaml
ansible.builtin.apt:        # not bare "apt"
ansible.builtin.service:
ansible.builtin.template:
ansible.builtin.apache2_module:
```

Benefits: explicit source, avoids ambiguity when collections grow.

---

## Privilege Escalation

Play-level (applies to all tasks):

```yaml
become: true
become_user: root    # optional, default root
become_method: sudo  # from ansible.cfg
```

Task-level override:

```yaml
- name: Read file as user
  ansible.builtin.command: cat /home/ubuntu/.profile
  become: false
```

---

## Validation Workflow

```bash
# 1. Syntax
ansible-playbook playbooks/apache.yml --syntax-check

# 2. List targets
ansible-playbook playbooks/apache.yml -i inventory/hosts.ini.local --list-hosts

# 3. Dry run
ansible-playbook playbooks/apache.yml -i inventory/hosts.ini.local --check

# 4. Apply
ansible-playbook playbooks/apache.yml -i inventory/hosts.ini.local

# 5. Verify
ansible webservers -i inventory/hosts.ini.local -b \
  -m ansible.builtin.command -a "systemctl is-active apache2"
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| YAML parse error | Indentation | Align under `tasks:` with spaces |
| `could not find or access` template | Wrong `src` path | Paths relative to playbook or role |
| Handler never runs | Task not `changed` or name mismatch | Check `notify` vs handler `name` |
| `Permission denied` | Missing `become` | Add `become: true` |
| `changed` every run | Wrong module args | Compare to module docs |
| Playbook targets wrong hosts | `hosts:` typo | `ansible-inventory --graph` |
| `ERROR! 'apt' is not a valid attribute` | Wrong YAML structure | Module name must be task key |

### PLAY RECAP Fields

```text
web1 : ok=3    changed=1    unreachable=0    failed=0    skipped=0
```

| Field | Meaning |
|-------|---------|
| `ok` | Tasks completed without change |
| `changed` | Tasks altered system |
| `unreachable` | SSH failure |
| `failed` | Task error |
| `skipped` | `when:` condition false |

---

## Related Lab Playbooks

| File | Topic |
|------|-------|
| `playbooks/apache.yml` | Tasks + handlers |
| `playbooks/vars-demo.yml` | Template module |
| `playbooks/role-site.yml` | Role invocation |
| `playbooks/nodejs.yml` | vars_files + vault |

---

## Hands-on Labs

| Lab | Topic | Manual |
|-----|-------|--------|
| Lab 04 | Apache playbook | [lab04](../../labmanuals/lab04-playbook-apache-webserver.md) |
| Lab 05 | Templates | [lab05](../../labmanuals/lab05-playbook-variables.md) |

**HTML companion:** [playbook-handlers.html](../../html/playbook-handlers.html)

---

## Production Practices

| Practice | Rationale |
|----------|-----------|
| One play per tier or concern | Easier limits and tags |
| Named tasks | Clear job output in AAP |
| Handlers for restarts | Avoid restart storms |
| `--check` in CI before apply | Catch unintended changes |
| `ansible-lint` on PRs | Style and bug patterns |

---

## Next Steps

1. Complete [Lab 04](../../labmanuals/lab04-playbook-apache-webserver.md).
2. Add variables and templates in [Ansible Variables](../05-variables/ansible-variables.md).
3. Package tasks into [Ansible Roles](../06-roles/ansible-roles.md).

---

## Quick Reference

```yaml
---
- name: Play title
  hosts: groupname
  become: true
  tasks:
    - name: Task title
      ansible.builtin.module_name:
        param: value
      notify: Handler name
  handlers:
    - name: Handler name
      ansible.builtin.service:
        name: servicename
        state: restarted
```

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/apache.yml
```
