# Static Inventory

Static inventory defines hosts and groups in files that you maintain in version control. For fixed lab environments and small fleets, INI or YAML inventory is simple, debuggable, and requires no cloud API access. This guide covers the patterns used in `ansible/extended/labs/inventory/hosts.ini`.

## Learning objectives

- Write INI and YAML inventory files
- Assign hosts to multiple groups and set group variables
- Verify inventory with `ansible-inventory`
- Organize `group_vars` and `host_vars` directories
- Know when to migrate to dynamic inventory

## Inventory file formats

Ansible accepts multiple inventory sources:

| Format | Extension | Best for |
|--------|-----------|----------|
| INI | `.ini`, no extension | Human-readable labs, quick edits |
| YAML | `.yml` | Complex structures, inline vars |
| Directory | `inventory/` folder | Large fleets with group_vars |
| Plugin | `aws_ec2.yml` | Dynamic cloud (see dynamic inventory doc) |

The extended labs use INI for static inventory and YAML for the AWS EC2 plugin.

## INI inventory anatomy

### Basic structure from extended labs

`labs/inventory/hosts.ini`:

```ini
[webservers]
web1 ansible_host=10.0.1.10
web2 ansible_host=11.0.1.11

[appservers]
app1 ansible_host=10.0.1.12

[webservers:vars]
ansible_user=ubuntu
ansible_python_interpreter=/usr/bin/python3

[appservers:vars]
ansible_user=ubuntu
ansible_python_interpreter=/usr/bin/python3
```

### INI syntax rules

| Element | Syntax | Example |
|---------|--------|---------|
| Group | `[groupname]` | `[webservers]` |
| Host | `hostname` or `hostname vars` | `web1 ansible_host=10.0.1.10` |
| Group variables | `[groupname:vars]` | `[webservers:vars]` |
| Child group | `[parent:children]` | `[production:children]` |
| Multiple groups | `:children` lists | `webservers` under `production` |

### Host variables inline

```ini
web1 ansible_host=10.0.1.10 ansible_port=22 ansible_user=ubuntu
```

Common connection variables:

| Variable | Purpose |
|----------|---------|
| `ansible_host` | IP or DNS to connect to (inventory name can differ) |
| `ansible_user` | SSH username |
| `ansible_port` | SSH port (default 22) |
| `ansible_ssh_private_key_file` | Path to private key |
| `ansible_python_interpreter` | Python on target (use `/usr/bin/python3` on Ubuntu 22.04) |
| `ansible_become` | Default privilege escalation |

## YAML inventory equivalent

```yaml
---
all:
  children:
    webservers:
      hosts:
        web1:
          ansible_host: 10.0.1.10
        web2:
          ansible_host: 10.0.1.11
      vars:
        ansible_user: ubuntu
        ansible_python_interpreter: /usr/bin/python3
    appservers:
      hosts:
        app1:
          ansible_host: 10.0.1.12
      vars:
        ansible_user: ubuntu
```

INI and YAML are interchangeable for most lab scenarios.

## Group hierarchy

```
all (implicit root)
├── webservers
│   ├── web1
│   └── web2
└── appservers
    └── app1
```

### Parent/child groups

```ini
[production:children]
webservers
appservers

[production:vars]
environment=production
```

Hosts in `webservers` and `appservers` inherit `production` variables.

## Verifying inventory

Always validate before running playbooks:

```bash
cd ~/terraform-ansible-labs/ansible/extended/labs

# Tree view of groups and hosts
ansible-inventory -i inventory/hosts.ini --graph

# Expected output:
# @webservers:
#   |--web1
#   |--web2
# @appservers:
#   |--app1

# Full JSON structure
ansible-inventory -i inventory/hosts.ini --list

# Show variables for one host
ansible-inventory -i inventory/hosts.ini --host web1

# YAML output
ansible-inventory -i inventory/hosts.ini --yaml
```

### Connectivity test

```bash
ansible -i inventory/hosts.ini all -m ansible.builtin.ping
```

## group_vars and host_vars

When inventory is a **directory**, Ansible auto-loads variables:

```
inventory/
  hosts.ini
  group_vars/
    all.yml
    webservers.yml
  host_vars/
    web1.yml
```

Extended labs place `group_vars/` beside playbooks:

```
labs/
  inventory/hosts.ini
  group_vars/
    all.yml
    webservers.yml
```

### group_vars/all.yml (from extended labs)

```yaml
---
nodejs_version: "20"
nodejs_app_port: 3000
nodejs_app_name: lab-app
```

These apply to **all** hosts when playbook references the inventory path.

### Loading behavior

| Location | Applies to |
|----------|------------|
| `group_vars/all.yml` | Every host |
| `group_vars/webservers.yml` | webservers group |
| `host_vars/web1.yml` | web1 only |
| `[group:vars]` in INI | That group |

## Inventory patterns in extended labs

### Static three-tier lab

| Group | Hosts | Role in curriculum |
|-------|-------|-------------------|
| webservers | web1, web2 | nginx, loops, handlers |
| appservers | app1 | Node.js application |

### Limiting execution

```bash
# Single host
ansible -i inventory/hosts.ini webservers -l web1 -m ansible.builtin.ping

# Multiple patterns
ansible-playbook -i inventory/hosts.ini site.yml --limit webservers
```

### Patterns in `hosts:` line

```yaml
hosts: webservers          # one group
hosts: web1:app1           # multiple hosts
hosts: all                 # entire inventory
hosts: webservers:&production  # intersection (advanced)
```

## ansible.cfg integration

`labs/ansible.cfg` may set default inventory:

```ini
[defaults]
inventory = inventory/hosts.ini
host_key_checking = False
retry_files_enabled = False
```

With defaults configured:

```bash
ansible webservers -m ansible.builtin.ping
ansible-playbook playbooks/site.yml
```

## Static vs dynamic inventory

| Aspect | Static | Dynamic |
|--------|--------|---------|
| IP management | Manual update | API-driven |
| Cloud credentials | Not required | AWS/GCP/Azure creds |
| Git-friendly | Yes — full file in repo | Plugin config in repo |
| ASG/scale events | Stale IPs | Auto-refresh |
| Lab suitability | Excellent | Requires AWS setup |

Use static inventory for extended labs 01–06 and 08. Lab 07 introduces dynamic AWS inventory.

## Troubleshooting

### UNREACHABLE hosts

```bash
# Test SSH manually
ssh -i ~/.ssh/lab.pem ubuntu@10.0.1.10

# Verbose Ansible
ansible -i inventory/hosts.ini web1 -m ping -vvv
```

| Symptom | Fix |
|---------|-----|
| Wrong IP | Update `ansible_host` in hosts.ini |
| Wrong user | Set `ansible_user=ubuntu` |
| Security group | Allow TCP 22 from control node |
| Key not found | Set `ansible_ssh_private_key_file` |

### Host not in expected group

```bash
ansible-inventory -i inventory/hosts.ini --graph
ansible-inventory -i inventory/hosts.ini --host web1 | jq .
```

### Variables not applied

- Confirm `group_vars/` path is correct relative to playbook or inventory
- Check filename matches group name exactly (`webservers.yml` not `webserver.yml`)
- YAML syntax errors silently skip — validate with `yamllint`

## Best practices

1. **Use meaningful inventory names** — `web1` not `10.0.1.10` as hostname
2. **Set `ansible_host`** when DNS name differs from inventory name
3. **Always set python3 interpreter** on Ubuntu 20.04+
4. **Keep secrets out of inventory** — use Ansible Vault for passwords
5. **Version control inventory** — track group membership changes in Git
6. **Document IP placeholders** — README explains replacing 10.0.x.x

## Inventory for break-fix lab

Drill 05 uses a broken inventory file:

```ini
# break-fix/drill-05-broken-inventory.ini
[webservers]
web1 ansible_host=10.0.1.10 ansible_python_interpreter=/usr/bin/python

[webservers:vars]
ansible_user=ubuntu
```

Fix: change interpreter to `/usr/bin/python3`.

## Related documentation

- [Dynamic Inventory on AWS](dynamic-inventory-aws.md)
- [Lab 01 — Ad Hoc](../../labmanuals/lab01-adhoc-modules.md)
- [Lab 07 — Dynamic Inventory](../../labmanuals/lab07-dynamic-inventory.md)
- Essentials: [inventory lab](../../../essentials/labmanuals/lab01-inventory-static-hosts.md)

## Quick reference

```bash
ansible-inventory -i inventory/hosts.ini --graph
ansible-inventory -i inventory/hosts.ini --list
ansible -i inventory/hosts.ini all -m ansible.builtin.ping
ansible-playbook -i inventory/hosts.ini playbooks/site.yml --limit webservers
```

## Summary

Static inventory in INI or YAML format lists hosts, groups, and connection variables explicitly. Verify with `ansible-inventory --graph`, layer variables via `group_vars`, and set `ansible_python_interpreter` for modern Ubuntu. Migrate to dynamic inventory when cloud instances change frequently.

---

*Ansible Extended Track · Lesson 6 · Curriculum v2*
