# Inventory: INI and YAML Formats

> **Curriculum:** Ansible Essentials · **Brand:** `#EE0000` · **Lab targets:** Ubuntu 22.04 · **SSH:** port 22

## Overview

Ansible inventory defines **which hosts** to manage, **how to group them**, and **connection variables** such as IP address, SSH user, and Python interpreter. The lab project ships two equivalent inventory files: INI format (`hosts.ini`) as the default, and YAML format (`hosts.yaml`) for teams that prefer structured data.

Inventory is the bridge between Terraform-provisioned infrastructure and Ansible configuration. After `terraform apply`, you map EC2 private IPs into inventory so playbooks target the correct hosts.

**Interactive reference:** [inventory-flow.html](../../html/inventory-flow.html)

---

## Key Concepts

| Term | Definition | Lab example |
|------|------------|-------------|
| **Host** | Single managed machine | `web1`, `web2`, `db1` |
| **Group** | Named collection of hosts | `webservers`, `dbservers` |
| **Parent group** | Group containing other groups | `all` (implicit root) |
| **Host variable** | Key-value on one host | `ansible_host=10.0.1.10` |
| **Group variable** | Key-value shared by group members | `[webservers:vars]` section |
| **Connection var** | How Ansible reaches the host | `ansible_user`, `ansible_host` |

### Inventory Variable Precedence (Host vs Group)

| Source | Scope | Example in lab |
|--------|-------|----------------|
| Host inline vars | Single host | `web1 ansible_host=10.0.1.10` |
| Group vars in inventory | All group members | `ansible_python_interpreter` under `[webservers:vars]` |
| `group_vars/` directory | All group members (file-based) | `group_vars/webservers.yml` |
| `host_vars/` directory | Single host (file-based) | Not used in lab (available pattern) |

Host-level variables override group-level variables for the same key.

---

## Lab Inventory Structure

```
inventory/
├── hosts.ini              ← default (ansible.cfg)
├── hosts.yaml             ← YAML equivalent
├── hosts.ini.local.example
└── group_vars/
    └── webservers.yml     ← webserver_port, app_env
```

### ansible.cfg Reference

```ini
[defaults]
inventory = inventory/hosts.ini
```

To use YAML inventory explicitly:

```bash
ansible-playbook playbooks/apache.yml -i inventory/hosts.yaml
```

---

## INI Format (`hosts.ini`)

Full lab inventory:

```ini
[webservers]
web1 ansible_host=10.0.1.10 ansible_user=ubuntu
web2 ansible_host=10.0.1.11 ansible_user=ubuntu

[webservers:vars]
ansible_python_interpreter=/usr/bin/python3

[dbservers]
db1 ansible_host=10.0.1.20 ansible_user=ubuntu
```

### INI Syntax Rules

| Element | Syntax | Notes |
|---------|--------|-------|
| Group header | `[groupname]` | Alphanumeric and underscore |
| Host line | `hostname var=value` | Hostname is inventory alias (not DNS name) |
| Group variables | `[groupname:vars]` | Applies to all hosts in group |
| Group children | `[parent:children]` | Nest groups (not in lab) |
| Comments | `;` or `#` at line start | |

### Connection Variables Explained

| Variable | Purpose | Lab value |
|----------|---------|-----------|
| `ansible_host` | IP or FQDN for SSH | `10.0.1.10` |
| `ansible_user` | SSH login user | `ubuntu` |
| `ansible_port` | SSH port | `22` (default, omitted) |
| `ansible_python_interpreter` | Python path on target | `/usr/bin/python3` |
| `ansible_ssh_private_key_file` | Path to PEM key | Set via env or `ansible.cfg` if needed |

---

## YAML Format (`hosts.yaml`)

Equivalent YAML inventory:

```yaml
all:
  children:
    webservers:
      hosts:
        web1:
          ansible_host: 10.0.1.10
          ansible_user: ubuntu
        web2:
          ansible_host: 10.0.1.11
          ansible_user: ubuntu
      vars:
        ansible_python_interpreter: /usr/bin/python3
    dbservers:
      hosts:
        db1:
          ansible_host: 10.0.1.20
          ansible_user: ubuntu
```

### INI vs YAML Comparison

| Aspect | INI (`hosts.ini`) | YAML (`hosts.yaml`) |
|--------|-------------------|---------------------|
| Readability | Compact for simple labs | Better for deep nesting |
| Syntax sensitivity | Forgiving | Indentation-sensitive |
| Dynamic generation | Easy to template | Native in Ansible Tower/AWX |
| Default in lab | Yes (`ansible.cfg`) | Alternate equivalent |
| Validation | `ansible-inventory --list` | Same command |

---

## Inventory Hierarchy Diagram

```
                              all (implicit)
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
              webservers                      dbservers
                    │                             │
         ┌──────────┼──────────┐                  │
         │          │          │                  │
       web1        web2      vars:              db1
    10.0.1.10   10.0.1.11  python3          10.0.1.20
         │          │                             │
         └──────────┴─────────────────────────────┘
                         │
              group_vars/webservers.yml
              ├── webserver_port: 80
              └── app_env: production
```

### Data Flow: Inventory to Playbook

```
hosts.ini / hosts.yaml
        │
        ▼
ansible-inventory --graph
        │
        ▼
playbook: hosts: webservers
        │
        ▼
Tasks execute on web1, web2 only
```

---

## group_vars Directory

File `inventory/group_vars/webservers.yml`:

```yaml
---
webserver_port: 80
app_env: production
```

Ansible automatically loads `group_vars/<groupname>.yml` when the group exists in inventory. These variables are available in playbooks targeting `webservers` and in templates like `templates/motd.j2`:

```jinja2
Welcome to {{ inventory_hostname }}
Environment: {{ app_env }}
Web port: {{ webserver_port }}
```

| Variable | Value | Used by |
|----------|-------|---------|
| `webserver_port` | `80` | `motd.j2`, future conditionals |
| `app_env` | `production` | `motd.j2`, `vars-demo.yml` |

---

## Inspecting Inventory

### Graph View

```bash
cd ansible/essentials/labs
ansible-inventory --graph
```

Expected output:

```
@all:
  |--@ungrouped:
  |--@webservers:
  |  |--web1
  |  |--web2
  |--@dbservers:
  |  |--db1
```

### JSON Dump (Full Variable Merge)

```bash
ansible-inventory --list
ansible-inventory --host web1
```

### Limit Execution to Subset

```bash
# Only web1
ansible-playbook playbooks/apache.yml --limit web1

# Only dbservers group
ansible dbservers -m ansible.builtin.ping
```

---

## FQCN Module Examples with Inventory

### Ping by Group

```bash
ansible webservers -m ansible.builtin.ping
ansible dbservers -m ansible.builtin.ping
ansible all -m ansible.builtin.ping
```

### Ad Hoc with Inventory Override

```bash
ansible webservers -m ansible.builtin.setup \
  -i inventory/hosts.yaml
```

### Playbook Host Patterns

From `playbooks/apache.yml`:

```yaml
- name: Install and configure Apache
  hosts: webservers
  become: true
```

| Pattern | Matches |
|---------|---------|
| `webservers` | All hosts in group |
| `web1` | Single host |
| `webservers:dbservers` | Union of groups |
| `webservers:!web2` | webservers except web2 |

---

## Mapping Terraform Outputs to Inventory

After Terraform provisions EC2 instances:

```
Terraform output          Inventory update
────────────────          ────────────────
web1_private_ip    ──►    web1 ansible_host=<ip>
web2_private_ip    ──►    web2 ansible_host=<ip>
db1_private_ip     ──►    db1 ansible_host=<ip>
```

```
┌─────────────┐    private IPs     ┌─────────────┐
│  Terraform  │ ────────────────► │  hosts.ini  │
│  apply      │                   │  (static)   │
└─────────────┘                   └──────┬──────┘
                                         │
                                         ▼
                                  ansible-playbook
```

For production, consider the `amazon.aws.aws_ec2` dynamic inventory plugin to auto-discover instances by tags.

---

## Troubleshooting

| Symptom | Likely cause | Resolution |
|---------|--------------|------------|
| `Could not match supplied host pattern` | Typo in group or host name | Run `ansible-inventory --graph`; check spelling |
| `UNREACHABLE` on one host only | Wrong `ansible_host` for that entry | Verify IP with `ping` or `ssh` |
| Variables undefined in template | Missing `group_vars` or wrong group | Confirm host is in `webservers`; check `group_vars/webservers.yml` |
| YAML inventory parse error | Indentation mistake | Validate with `ansible-inventory -i hosts.yaml --list` |
| Wrong host targeted | Broad `hosts:` pattern | Use `--limit` for testing |
| `ansible_host` ignored | Variable on wrong line in INI | Put vars on same line as hostname or in `[group:vars]` |
| Group vars not loading | File not in `group_vars/` or wrong name | File must be `group_vars/webservers.yml` for group `webservers` |
| Two inventory files conflict | Multiple `-i` sources | Understand merge order; prefer single source |

### Diagnostic Commands

```bash
# Verify effective host variables
ansible-inventory --host web1

# Test SSH connectivity outside Ansible
ssh -i ~/.ssh/lab-key.pem -p 22 ubuntu@10.0.1.10

# Verbose inventory parsing
ansible-inventory --list -vvv
```

---

## Hands-on Labs

| Lab | Topic | Manual |
|-----|-------|--------|
| Lab 01 | Static inventory file | [lab01-inventory-static-hosts.md](../../labmanuals/lab01-inventory-static-hosts.md) |
| Lab 02 | Hosts, groups, and vars | [lab02-inventory-hosts-groups.md](../../labmanuals/lab02-inventory-hosts-groups.md) |
| Lab 03 | Ad hoc against inventory | [lab03-adhoc-commands.md](../../labmanuals/lab03-adhoc-commands.md) |

**HTML companion:** [inventory-flow.html](../../html/inventory-flow.html)

---

## Next Steps

1. Practice ad hoc commands against inventory groups in [Ad Hoc Commands](../03-adhoc/adhoc-commands.md).
2. Write your first playbook targeting `webservers` in [Playbook and YAML Basics](../04-playbooks/playbook-and-yaml-basics.md).
3. Learn how `group_vars` feeds templates in [Ansible Variables](../05-variables/ansible-variables.md).
4. Complete Lab 01 and Lab 02 to validate both INI and YAML inventories.
