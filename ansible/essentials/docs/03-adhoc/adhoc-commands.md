# Ad Hoc Commands

> **Curriculum:** Ansible Essentials · **Brand:** `#EE0000` · **Lab targets:** Ubuntu 22.04 · **SSH:** port 22

## Overview

Ad hoc commands run a **single Ansible module** against a **host pattern** from the shell—no playbook file required. They are the fastest way to test connectivity, inspect remote state, apply one-off fixes, and explore facts before codifying tasks in version-controlled playbooks.

Syntax:

```bash
ansible <host-pattern> -i <inventory> [-b] -m <module> -a "<arguments>"
```

Add `-b` (become) when the module needs root privileges—for example `ansible.builtin.apt` on Ubuntu. Prefer **FQCN** module names (`ansible.builtin.ping`) over short names (`ping`) for clarity and forward compatibility.

**Interactive reference:** [adhoc-vs-playbook.html](../../html/adhoc-vs-playbook.html)

---

## Key Concepts

| Term | Definition | Example |
|------|------------|---------|
| **Host pattern** | Which hosts to target | `webservers`, `web1`, `all` |
| **Inventory** | Host list and connection vars | `-i inventory/hosts.ini.local` |
| **Module** | Unit of work Ansible executes | `ansible.builtin.command` |
| **Arguments** | Module parameters as string | `-a "name=tree state=present"` |
| **Become** | Privilege escalation (sudo) | `-b` flag |
| **Forks** | Parallel SSH sessions | `-f 10` (default 5) |

### Ad Hoc vs Playbook

| Dimension | Ad hoc | Playbook |
|-----------|--------|----------|
| **Storage** | Shell history only | Git repository |
| **Tasks per invocation** | One module | Many tasks, handlers |
| **Review / audit** | Poor | Pull request friendly |
| **Idempotency** | Per module | Entire desired state |
| **Best for** | Quick checks, emergencies | Production automation |
| **Lab** | [lab03](../../labmanuals/lab03-adhoc-commands.md) | [lab04](../../labmanuals/lab04-playbook-apache-webserver.md) |

### Execution Flow

```
Control node                          Managed node
────────────                          ────────────
ansible web1 -m ping
       │
       ├── resolve pattern via inventory
       ├── SSH connect (ansible_user, ansible_host)
       ├── transfer module + args
       ├── Python executes module
       ◄── JSON result (ok/changed/failed)
       └── print per-host summary
```

---

## Common Modules (Ubuntu Lab)

| Use case | FQCN module | Example |
|----------|-------------|---------|
| Connectivity | `ansible.builtin.ping` | `ansible all -m ansible.builtin.ping` |
| Shell command | `ansible.builtin.command` | `-a "uptime"` |
| Package (Debian) | `ansible.builtin.apt` | `-b -a "name=apache2 state=present"` |
| Service | `ansible.builtin.service` | `-b -a "name=apache2 state=started"` |
| Copy content | `ansible.builtin.copy` | `-b -a "content='hi' dest=/tmp/hi.txt"` |
| File manage | `ansible.builtin.file` | `-b -a "path=/tmp/hi.txt state=absent"` |
| Template | `ansible.builtin.template` | Usually in playbooks |
| Facts | `ansible.builtin.setup` | `-a "filter=ansible_distribution*"` |
| Debug | `ansible.builtin.debug` | `-a "var=app_env"` |
| HTTP check | `ansible.builtin.uri` | `-a "url=http://localhost/ status_code=200"` |

On Ubuntu targets, use `apt`—not `yum` or `dnf` examples from RHEL-centric training.

---

## Host Patterns

| Pattern | Matches | Lab example |
|---------|---------|-------------|
| `all` | Every host in inventory | 3 hosts if db1 exists |
| `webservers` | Group members | web1, web2 |
| `web1` | Single host | One host |
| `webservers:dbservers` | Union | All tiers |
| `webservers:!web2` | Exclusion | web1 only |
| `*.example.com` | Wildcard | DNS-style names |

```bash
cd ansible/essentials/labs
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.ping
ansible web1:web2 -i inventory/hosts.ini.local -m ansible.builtin.ping
```

---

## Privilege Escalation

```bash
# Without -b: runs as ansible_user (ubuntu)
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.apt -a "name=tree state=present"
# → FAIL: permission denied

# With -b: uses sudo per ansible.cfg
ansible web1 -i inventory/hosts.ini.local -b \
  -m ansible.builtin.apt -a "name=tree state=present update_cache=yes"
# → SUCCESS
```

`ansible.cfg` in the lab sets:

```ini
[privilege_escalation]
become_method = sudo
```

Equivalent playbook keyword: `become: true`.

---

## Example Session (Lab Paths)

```bash
cd ~/terraform-ansible-labs/ansible/essentials/labs

# 1. Connectivity
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.ping

# 2. Read-only command
ansible webservers -i inventory/hosts.ini.local \
  -m ansible.builtin.command -a "uptime"

# 3. Package install (become)
ansible web1 -i inventory/hosts.ini.local -b \
  -m ansible.builtin.apt -a "name=tree state=present update_cache=yes"

# 4. Verify
ansible web1 -i inventory/hosts.ini.local \
  -m ansible.builtin.command -a "which tree"

# 5. Facts
ansible web1 -i inventory/hosts.ini.local \
  -m ansible.builtin.setup -a "filter=ansible_memtotal_mb"

# 6. Debug group var
ansible webservers -i inventory/hosts.ini.local \
  -m ansible.builtin.debug -a "var=webserver_port"

# 7. Cleanup
ansible web1 -i inventory/hosts.ini.local -b \
  -m ansible.builtin.apt -a "name=tree state=absent"
```

---

## Output Interpretation

| Status | Meaning | Action |
|--------|---------|--------|
| `SUCCESS` / `ok` | Module ran; no change needed | None |
| `CHANGED` | Module altered system | Expected on first package install |
| `FAILED` | Module error | Read message; fix args or permissions |
| `UNREACHABLE` | SSH/connection failure | Fix inventory IP, keys, security groups |
| `SKIPPED` | Condition not met | Normal with `when:` in playbooks |

Example ping output:

```text
web1 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

`ansible.builtin.ping` does **not** use ICMP—it verifies Ansible can execute Python over SSH.

---

## Troubleshooting Flags

| Flag | Purpose |
|------|---------|
| `-v`, `-vv`, `-vvv` | Increase verbosity (SSH details at `-vvv`) |
| `--limit web1` | Restrict to subset |
| `--check` | Dry run (module support varies) |
| `-f 1` | Serial execution (one host at a time) |
| `-u root` | Override remote user |
| `-e "var=value"` | Extra variable (playbooks more common) |

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.ping -vvv
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.apt \
  -b -a "name=sl state=present" --check
```

---

## Module Documentation

```bash
ansible-doc -t module ansible.builtin.apt
ansible-doc -t module ansible.builtin.service
ansible-doc -l | grep ansible.builtin
```

Always check required parameters before guessing `-a` string format.

---

## When to Promote to Playbook

| Signal | Action |
|--------|--------|
| Same command run twice | Write playbook |
| Multiple steps in sequence | Write playbook |
| Needs handler on change | Write playbook |
| Team must review in Git | Write playbook |
| One-time ping during incident | Keep ad hoc |

---

## Troubleshooting

| Symptom | Likely cause | Resolution |
|---------|--------------|------------|
| `sudo: a password is required` | Missing `-b` or NOPASSWD | Add `-b`; configure sudoers |
| `Could not find apt` | Non-Debian target | Use correct package module |
| `UNREACHABLE` | Wrong IP or SG | Lab 01 connectivity steps |
| `Module not found: ping` | Old Ansible | Use `ansible.builtin.ping` |
| `Failed to lock apt` | Concurrent apt | Wait and retry |
| `command` shows CHANGED always | Module limitation | Use dedicated module if exists |
| Wrong host targeted | Pattern typo | `ansible-inventory --graph` |
| Variable undefined in debug | Not in scope for ad hoc | Use playbook or `-e` |

### Diagnostic Commands

```bash
ansible-inventory -i inventory/hosts.ini.local --graph
ansible-inventory -i inventory/hosts.ini.local --host web1
ssh -o ConnectTimeout=5 ubuntu@<ip> "hostname"
```

---

## Hands-on Labs

| Lab | Topic | Manual |
|-----|-------|--------|
| Lab 01 | Ping via inventory | [lab01](../../labmanuals/lab01-inventory-static-hosts.md) |
| Lab 03 | Ad hoc deep dive | [lab03](../../labmanuals/lab03-adhoc-commands.md) |
| Lab 04 | Playbook alternative | [lab04](../../labmanuals/lab04-playbook-apache-webserver.md) |

**HTML companion:** [adhoc-vs-playbook.html](../../html/adhoc-vs-playbook.html)

---

## Production Notes

| Lab habit | Production practice |
|-----------|---------------------|
| Ad hoc package installs | Playbook + CI pipeline |
| Shared control node | AWX / Ansible Automation Platform |
| `-b` on CLI | `become: true` in playbook |
| No logging | Audit trail in AAP job output |

---

## Next Steps

1. Complete [Lab 03 — Ad hoc commands](../../labmanuals/lab03-adhoc-commands.md).
2. Learn repeatable automation in [Playbook and YAML Basics](../04-playbooks/playbook-and-yaml-basics.md).
3. Compare workflows in [adhoc-vs-playbook.html](../../html/adhoc-vs-playbook.html).

---

## Quick Reference

```bash
ansible <pattern> -i inventory/hosts.ini.local -m ansible.builtin.<module> -a "<args>"
ansible <pattern> -i inventory/hosts.ini.local -b -m ansible.builtin.apt -a "name=PKG state=present"
ansible <pattern> -i inventory/hosts.ini.local -m ansible.builtin.setup -a "filter=ansible_distribution*"
```
