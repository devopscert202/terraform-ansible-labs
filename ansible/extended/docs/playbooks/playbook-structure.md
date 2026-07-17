# Playbook Structure

Ansible playbooks are YAML files describing **what** should happen on **which** hosts in **what order**. Playbooks are the foundation of repeatable automation — ad hoc commands (Lab 01) are for exploration; playbooks are for production. This guide covers anatomy, conventions, and validation used throughout the extended track.

## Learning objectives

- Read and write multi-play YAML playbooks
- Apply FQCN module names consistently
- Configure play-level `become`, `vars`, and `handlers`
- Validate playbooks before execution
- Understand idempotency expectations

## Playbook vs ad hoc

| Aspect | Ad hoc | Playbook |
|--------|--------|----------|
| Command | `ansible -m ...` | `ansible-playbook site.yml` |
| Repeatability | Shell history | Version-controlled YAML |
| Complexity | Single module | Tasks, handlers, roles |
| Use case | Quick checks | Production automation |

## Minimal playbook

```yaml
---
- name: Install curl on webservers
  hosts: webservers
  become: true
  tasks:
    - name: Ensure curl is installed
      ansible.builtin.apt:
        name: curl
        state: present
```

### Execution

```bash
ansible-playbook --syntax-check playbooks/example.yml
ansible-playbook -i inventory/hosts.ini playbooks/example.yml
```

## Play anatomy

```yaml
---
- name: Human-readable play name          # Play 1
  hosts: webservers                        # Target pattern
  become: true                             # Privilege escalation
  gather_facts: true                       # Default — setup module
  vars:                                    # Play variables
    package_name: nginx
  tasks:                                   # Ordered task list
    - name: Install package
      ansible.builtin.apt:
        name: "{{ package_name }}"
        state: present
  handlers:                                # Notified tasks (end of play)
    - name: Restart service
      ansible.builtin.service:
        name: nginx
        state: restarted
```

### Key elements

| Key | Required | Purpose |
|-----|----------|---------|
| `hosts` | Yes | Inventory pattern: group, host, `all`, or pattern |
| `tasks` | Yes* | List of modules to execute |
| `name` | Recommended | Displayed in output for plays and tasks |
| `become` | No | `true` for sudo/root tasks |
| `vars` | No | Play-scoped variables |
| `handlers` | No | Tasks triggered by `notify` |
| `gather_facts` | No | Default `true` |
| `serial` | No | Rolling update batch size |
| `tags` | No | Selective execution |

*Plays can use `roles` instead of explicit `tasks`.

## Multi-play playbooks

`labs/playbooks/site.yml` orchestrates multiple tiers:

```yaml
---
- name: Configure web tier
  hosts: webservers
  become: true
  roles:
    - common
    - webserver

- name: Configure app tier
  hosts: appservers
  become: true
  roles:
    - common
    - nodejs_app
```

Each play runs independently — facts re-gathered per play by default.

## FQCN modules (required convention)

Ansible 2.10+ uses collections. Always specify fully qualified collection names:

| Avoid | Use |
|-------|-----|
| `apt` | `ansible.builtin.apt` |
| `service` | `ansible.builtin.service` |
| `template` | `ansible.builtin.template` |
| `copy` | `ansible.builtin.copy` |
| `ping` | `ansible.builtin.ping` |
| `yum` | `ansible.builtin.yum` or `ansible.builtin.dnf` |

Benefits:
- No ambiguity when multiple collections provide similar modules
- Future-proof against deprecation warnings
- Clear in code review which implementation runs

## Task structure

```yaml
- name: Descriptive task name
  ansible.builtin.module_name:
    param1: value
    param2: "{{ variable }}"
  when: condition | default(true)
  notify: Handler name
  tags:
    - deploy
  register: result_var
```

### Naming tasks

Always provide `name:` — output shows task names during runs and failures:

```text
TASK [Ensure curl is installed] ************************
ok: [web1]
```

Unnamed tasks show module name only — harder to debug.

## Variables in playbooks

### Play vars

```yaml
vars:
  nodejs_version: "20"
  nodejs_app_port: 3000
```

### Referencing variables

```yaml
- ansible.builtin.debug:
    msg: "Port is {{ nodejs_app_port }}"
```

### Inventory and group_vars

Variables in `group_vars/all.yml` merge with play vars. See [variables guide](variables-and-templates.md) for precedence.

## Idempotency

A well-written playbook produces **no changes** on second run when state is already correct.

```bash
ansible-playbook -i inventory/hosts.ini playbooks/nodejs.yml
# First run: changed=15

ansible-playbook -i inventory/hosts.ini playbooks/nodejs.yml
# Second run: changed=0 (mostly ok)
```

Modules report:
- `changed` — state was modified
- `ok` — already in desired state
- `failed` — error occurred
- `skipped` — `when` condition false

Design tasks for desired state: `state: present`, not `shell: apt install`.

## Validation workflow

### Syntax check

```bash
ansible-playbook --syntax-check playbooks/nodejs.yml
```

Catches YAML errors without connecting to hosts.

### Check mode (dry run)

```bash
ansible-playbook -i inventory/hosts.ini playbooks/nodejs.yml --check
```

Simulates changes — not all modules support check mode fully.

### Diff mode

```bash
ansible-playbook -i inventory/hosts.ini playbooks/handlers-nginx.yml --check --diff
```

Shows file differences for template/copy modules.

### List tasks

```bash
ansible-playbook -i inventory/hosts.ini playbooks/site.yml --list-tasks
ansible-playbook -i inventory/hosts.ini playbooks/site.yml --list-hosts
```

## Extended lab playbooks

| File | Purpose | Lab |
|------|---------|-----|
| `nodejs.yml` | Node.js 20 + systemd app | 03 |
| `loops-packages.yml` | loop over packages/users | 04 |
| `conditionals-os.yml` | when with facts/groups | 05 |
| `handlers-nginx.yml` | notify and handlers | 06 |
| `site.yml` | Multi-role deployment | 08 |

### nodejs.yml highlights

- NodeSource repository with GPG keyring (no deprecated `apt_key`)
- Jinja2 templates for app and systemd unit
- Handlers restart application on file change
- Targets `appservers` group

## Common patterns

### Ensure package installed

```yaml
- ansible.builtin.apt:
    name: nginx
    state: present
    update_cache: true
```

### Deploy template

```yaml
- ansible.builtin.template:
    src: nginx.conf.j2
    dest: /etc/nginx/sites-available/lab.conf
    mode: "0644"
    validate: nginx -t -f %s
  notify: Reload nginx
```

### Include role

```yaml
roles:
  - role: webserver
    vars:
      webserver_port: 8080
```

## Error handling

### Block/rescue (advanced)

```yaml
- block:
    - ansible.builtin.command: /bin/false
  rescue:
    - ansible.builtin.debug:
        msg: "Task failed but play continues"
```

### any_errors_fatal

```yaml
- hosts: all
  any_errors_fatal: true
```

## ansible.cfg interaction

`labs/ansible.cfg`:

```ini
[defaults]
inventory = inventory/hosts.ini
host_key_checking = False
```

Playbook path relative to `labs/` directory when executing from there.

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `ERROR! Syntax Error` | YAML indent | Align with spaces, no tabs |
| `couldn't resolve module` | Missing FQCN | Use `ansible.builtin.*` |
| `template not found` | Wrong path | `src` relative to `templates/` |
| `Permission denied` | Missing become | `become: true` |
| `host not in inventory` | Wrong group | Check `ansible-inventory --graph` |

## Best practices

1. **One play per tier** — webservers, appservers, databases separately
2. **FQCN always** — avoid deprecation warnings
3. **Name every play and task** — operational clarity
4. **Syntax-check in CI** — before any deploy
5. **Idempotent modules** — prefer `apt` over `shell apt-get`
6. **Version control** — playbooks in Git with review
7. **Limit blast radius** — `--limit` for canary deploys

## Related documentation

- [Loops and Conditionals](loops-and-conditionals.md)
- [Handlers and Notify](handlers-notify.md)
- [Variables and Templates](variables-and-templates.md)
- [Lab 03 — Node.js](../../labmanuals/lab03-nodejs-playbook.md)
- [Lab 08 — Roles](../../labmanuals/lab08-roles-project.md)

## Quick reference

```bash
cd ~/terraform-ansible-labs/ansible/extended/labs
ansible-playbook --syntax-check playbooks/site.yml
ansible-playbook -i inventory/hosts.ini playbooks/site.yml
ansible-playbook -i inventory/hosts.ini playbooks/site.yml --check --diff
ansible-playbook -i inventory/hosts.ini playbooks/site.yml --limit web1
ansible-playbook -i inventory/hosts.ini playbooks/site.yml -e "var=value"
```

## Summary

Playbooks structure automation as YAML plays containing tasks, variables, and handlers. Use FQCN modules, meaningful names, and `become` where root is required. Validate with `--syntax-check` and `--check` before production runs. Extended labs progress from simple playbooks (nodejs.yml) to multi-role site.yml.

---

*Ansible Extended Track · Lesson 5 · Curriculum v2*
