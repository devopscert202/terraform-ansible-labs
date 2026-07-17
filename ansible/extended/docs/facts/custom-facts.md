# Custom Facts

Custom facts extend Ansible's built-in discovery with **site-specific metadata** — application tier, cost center, deployment environment, or version strings that only your organization knows. They live on managed nodes in `/etc/ansible/facts.d/` and appear under the `ansible_local` namespace after fact gathering.

## Learning objectives

- Deploy INI and JSON custom fact files with Ansible
- Execute custom fact scripts safely
- Access `ansible_local` variables in playbooks and templates
- Know when to use custom facts vs inventory variables vs group_vars

## Custom facts vs other variable sources

| Source | Scope | Changes when | Best for |
|--------|-------|--------------|----------|
| `group_vars/` | Inventory group | You edit Git | Static config per tier |
| `host_vars/` | Single host | You edit Git | Host-specific overrides |
| Custom facts (`ansible_local`) | Managed node | File on host changes | Data that lives on the node |
| `setup` default facts | Managed node | Each gather | OS, hardware, network |

Use custom facts when the value is **maintained on the host** or set by another provisioning tool. Use inventory variables when the control node is the source of truth.

## The custom facts pipeline

```
Deploy to /etc/ansible/facts.d/
    │
    ├── static_file.fact (INI or JSON)
    │
    └── executable_script (outputs JSON to stdout)
    │
    ▼
setup module runs (play start or manual)
    │
    ▼
Scripts executed; files parsed
    │
    ▼
Merged into ansible_local.<filename>
    │
    ▼
Available as ansible_local.section.key
```

## File location and naming

| Rule | Detail |
|------|--------|
| Directory | `/etc/ansible/facts.d/` (must exist) |
| Extension | `.fact` for static files; executable scripts also use `.fact` |
| Permissions | Static files: readable; scripts: executable (`0755`) |
| Naming | Filename (without extension) becomes `ansible_local` key |

Example: `/etc/ansible/facts.d/lab.fact` → `ansible_local.lab.*`

## INI format facts

INI is the simplest format for static metadata.

### File content

`/etc/ansible/facts.d/lab.fact`:

```ini
[lab]
tier=web
course=extended
environment=dev

[compliance]
pci=false
owner=platform-team
```

### Resulting variables

After `ansible.builtin.setup`:

```yaml
ansible_local:
  lab:
    tier: web
    course: extended
    environment: dev
  compliance:
    pci: false
    owner: platform-team
```

### Access in playbook

```yaml
- name: Show tier
  ansible.builtin.debug:
    msg: "Host {{ inventory_hostname }} is tier {{ ansible_local.lab.tier }}"

- name: Apply web-only role
  ansible.builtin.include_role:
    name: webserver
  when: ansible_local.lab.tier == "web"
```

## JSON format facts

JSON files must contain valid JSON objects:

`/etc/ansible/facts.d/app.fact`:

```json
{
    "version": "2.4.1",
    "build": "20240315",
    "features": {
        "metrics": true,
        "tracing": false
    }
}
```

Access: `ansible_local.app.version`, `ansible_local.app.features.metrics`

## Executable fact scripts

Scripts run during setup and must print **valid JSON** to stdout.

### Example script

`/etc/ansible/facts.d/uptime.fact`:

```bash
#!/bin/bash
echo "{\"uptime_seconds\": $(cut -d. -f1 /proc/uptime)}"
```

```bash
chmod 0755 /etc/ansible/facts.d/uptime.fact
```

### Security warning

Any user who can write to `facts.d` can execute code as the user Ansible connects with during setup. Restrict directory permissions:

```yaml
- ansible.builtin.file:
    path: /etc/ansible/facts.d
    state: directory
    mode: "0755"
    owner: root
    group: root
```

## Deploying custom facts with Ansible

### Lab 02 pattern — copy INI file

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.copy \
  -a 'dest=/etc/ansible/facts.d/lab.fact mode=0755 content="[lab]\ntier=web\ncourse=extended\n"'
```

### Playbook task

```yaml
---
- name: Deploy custom facts
  hosts: webservers
  become: true
  tasks:
    - name: Ensure facts.d directory exists
      ansible.builtin.file:
        path: /etc/ansible/facts.d
        state: directory
        mode: "0755"

    - name: Deploy lab metadata fact
      ansible.builtin.copy:
        dest: /etc/ansible/facts.d/lab.fact
        mode: "0644"
        content: |
          [lab]
          tier=web
          course=extended
        notify: Refresh facts

  handlers:
    - name: Refresh facts
      ansible.builtin.setup:
```

### Template-based facts

For per-host values without separate host_vars files:

```yaml
- ansible.builtin.template:
    src: host-meta.fact.j2
    dest: /etc/ansible/facts.d/host-meta.fact
    mode: "0644"
```

`templates/host-meta.fact.j2`:

```ini
[lab]
tier={{ host_tier | default('standard') }}
hostname={{ inventory_hostname }}
```

## Re-gathering facts after deployment

Custom facts are **not** automatically refreshed when files change mid-play.

```yaml
# Required after deploying new fact files
- ansible.builtin.setup:
```

Or start a new play (automatic gather at play start).

### Ad hoc refresh

```bash
ansible -i inventory/hosts.ini webservers -m ansible.builtin.setup
ansible -i inventory/hosts.ini webservers -m ansible.builtin.debug \
  -a "var=ansible_local.lab"
```

Expected output:

```json
{
    "ansible_local": {
        "lab": {
            "tier": "web",
            "course": "extended"
        }
    }
}
```

## Validation checklist

```bash
# 1. File exists on target
ansible web1 -i inventory/hosts.ini -b -m ansible.builtin.command \
  -a "cat /etc/ansible/facts.d/lab.fact"

# 2. Re-gather facts
ansible webservers -i inventory/hosts.ini -m ansible.builtin.setup

# 3. Verify ansible_local
ansible webservers -i inventory/hosts.ini -m ansible.builtin.debug \
  -a "var=ansible_local.lab"

# 4. Use in conditional (dry run)
ansible web1 -i inventory/hosts.ini -m ansible.builtin.debug \
  -a "msg=tier is {{ ansible_local.lab.tier | default('UNDEFINED') }}"
```

## Troubleshooting

### `ansible_local` is undefined

| Cause | Fix |
|-------|-----|
| Facts not re-gathered after deploy | Run `setup` module |
| Wrong file extension | Must be `.fact` |
| Invalid INI/JSON syntax | Validate file content on host |
| File in wrong directory | Must be `/etc/ansible/facts.d/` |

### Script facts return nothing

| Cause | Fix |
|-------|-----|
| Not executable | `chmod +x script.fact` |
| Invalid JSON output | Test script manually: `./script.fact` |
| Shebang missing | Add `#!/bin/bash` or `#!/usr/bin/python3` |
| stderr pollution | Redirect errors; only JSON to stdout |

### Permission denied deploying facts

Use `become: true` — `/etc/ansible/facts.d/` is root-owned.

## Custom facts vs fact modules

| Approach | When to use |
|----------|-------------|
| Static `.fact` file | Fixed metadata (tier, env) |
| Executable `.fact` | Dynamic values from local commands |
| `setup` subsets | Standard OS/hardware/network |
| `set_fact` module | Runtime variables during play (not persisted) |
| `register` | Capture task output for later tasks |

`set_fact` does not survive across plays unless cached. Custom facts persist on disk until removed.

## Production patterns

### Tier-based automation

```yaml
- name: Web tier hardening
  ansible.builtin.include_tasks: harden-web.yml
  when: ansible_local.metadata.tier | default('') == "web"
```

### Compliance tagging

```ini
[compliance]
data_class=confidential
retention_days=90
```

### Integration with CMDB

An executable fact script queries local agent or API:

```python
#!/usr/bin/env python3
import json, subprocess
# Output CMDB attributes as JSON
print(json.dumps({"cmdb_id": "SRV-12345", "owner": "team-a"}))
```

## Cleanup

Remove lab facts after exercises:

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.file \
  -a "path=/etc/ansible/facts.d/lab.fact state=absent"
```

## Design guidelines

1. **Keep facts small** — large JSON slows setup on every host
2. **Version schema** — add `schema_version=1` in INI for migrations
3. **Document keys** — maintain a schema in your repo README
4. **Prefer inventory for static fleet data** — custom facts for node-local truth
5. **Test scripts idempotently** — same output on repeated runs

## Related resources

- [Gathering Facts](gathering-facts.md) — setup module and default facts
- [Lab 02 — Facts](../../labmanuals/lab02-facts.md) — deploy `lab.fact` exercise
- [facts.html](../../html/facts.html) — interactive custom facts flow diagram
- Ansible docs: *Local facts* in setup module documentation

## Summary

Custom facts in `/etc/ansible/facts.d/` extend `ansible_local` with organization-specific metadata. Deploy with `copy` or `template`, set correct permissions, re-run `setup`, and reference `ansible_local.<file>.<key>` in playbooks. Use executable scripts sparingly and securely for dynamic values.

---

*Ansible Extended Track · Lesson 3 AP-03 · Curriculum v2*
