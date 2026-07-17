# Lab 01: Executing Ansible Modules (Ad Hoc)

> **Goal:** Run production-style modules from the command line without playbooks — package install, service control, file copy, and user management.
> **Time:** ~45 min · **Files:** `labs/inventory/hosts.ini` · **Source:** Lesson 3 AP-02

## Before you start

- [AWS lab environment](../../../curriculum/setup/aws-lab-environment.md) complete
- [Ansible essentials lab01–lab02](../../essentials/labmanuals/lab01-inventory-static-hosts.md) complete
- SSH from control node to `web1` and `web2` works
- Working directory: `~/terraform-ansible-labs/ansible/extended/labs`

## Concepts

| Term | Meaning |
|------|---------|
| Ad hoc | One-off command using `-m` (module) |
| FQCN | Fully qualified collection name, e.g. `ansible.builtin.apt` |
| `-a` | Module arguments (key=value pairs or JSON) |
| `-b` / `--become` | Run with privilege escalation (sudo) |

Ad hoc commands are ideal for quick checks. Repeatable configuration belongs in playbooks (lab03+).

---

## Steps

### Step 1 — Enter the lab directory and verify inventory

```bash
cd ~/terraform-ansible-labs/ansible/extended/labs
cat inventory/hosts.ini
```

Edit `inventory/hosts.ini` and replace placeholder IPs (`10.0.1.10`, `10.0.1.11`, `10.0.1.12`) with your Ubuntu 22.04 private IPs.

**Validate**

```bash
ansible-inventory -i inventory/hosts.ini --graph
```

```text
@webservers:
  |--web1
  |--web2
@appservers:
  |--app1
```

You see both groups with three hosts total.

---

### Step 2 — Connectivity with `ansible.builtin.ping`

```bash
ansible -i inventory/hosts.ini webservers -m ansible.builtin.ping
```

**Validate**

```text
web1 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
web2 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

Both hosts return `pong`. If either shows `UNREACHABLE`, fix SSH before continuing.

---

### Step 3 — Run a shell command with `ansible.builtin.command`

```bash
ansible -i inventory/hosts.ini webservers -m ansible.builtin.command -a "hostname -f"
```

**Validate**

Each host prints its hostname. `changed` should be `false` (commands do not claim idempotent change by default).

```text
web1 | CHANGED | rc=0 >>
web1
```

> **Note:** Prefer `ansible.builtin.command` over raw `shell` when you do not need pipes or redirects.

---

### Step 4 — Install a package with `ansible.builtin.apt`

Package management requires root. Use `--become`:

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.apt \
  -a "name=curl state=present update_cache=yes"
```

**Validate**

```text
web1 | CHANGED =>
web2 | CHANGED =>
```

Or `SUCCESS` with `changed: false` on a second run (idempotent).

Verify on one host:

```bash
ansible -i inventory/hosts.ini web1 -m ansible.builtin.command -a "curl --version"
```

```text
curl 7.81.0 ...
```

---

### Step 5 — Manage a service with `ansible.builtin.service`

Install nginx, then ensure it is running:

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.apt \
  -a "name=nginx state=present"

ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.service \
  -a "name=nginx state=started enabled=yes"
```

**Validate**

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.command \
  -a "systemctl is-active nginx"
```

```text
web1 | CHANGED | rc=0 >>
active
web2 | CHANGED | rc=0 >>
active
```

---

### Step 6 — Copy a file with `ansible.builtin.copy`

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.copy \
  -a "content='Configured by Ansible ad hoc lab\n' dest=/tmp/adhoc-marker.txt mode=0644"
```

**Validate**

```bash
ansible -i inventory/hosts.ini webservers -m ansible.builtin.command \
  -a "cat /tmp/adhoc-marker.txt"
```

```text
Configured by Ansible ad hoc lab
```

---

### Step 7 — Create a user with `ansible.builtin.user`

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.user \
  -a "name=labops shell=/bin/bash create_home=yes"
```

**Validate**

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.command \
  -a "id labops"
```

```text
uid=... labops ...
```

---

### Step 8 — Limit execution to one host

```bash
ansible -i inventory/hosts.ini webservers -l web1 -m ansible.builtin.debug \
  -a "msg=Hello from {{ inventory_hostname }}"
```

**Validate**

Only `web1` appears in output.

```text
web1 | SUCCESS => {
    "msg": "Hello from web1"
}
```

---

### Step 9 — Parallelism with `-f`

```bash
ansible -i inventory/hosts.ini webservers -f 2 -m ansible.builtin.ping
```

**Validate**

Both hosts still succeed. `-f` controls fork count (default is 5).

---

### Step 10 — Dry-run with `--check` (where supported)

```bash
ansible -i inventory/hosts.ini webservers -b --check -m ansible.builtin.apt \
  -a "name=tree state=present"
```

**Validate**

Output shows `changed` **would** occur or reports simulated state. Some modules fully support check mode; others show warnings.

---

### Step 11 — Verbose mode for debugging

When a command fails, add verbosity to see SSH and module details:

```bash
ansible -i inventory/hosts.ini web1 -m ansible.builtin.ping -vvv 2>&1 | tail -30
```

**Validate**

Output includes `ESTABLISH SSH CONNECTION` and Python interpreter path. No `UNREACHABLE` or `FAILED` lines.

---

### Step 12 — File module: ensure directory exists

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.file \
  -a "path=/opt/lab-demo state=directory mode=0755 owner=ubuntu"
```

**Validate**

```bash
ansible -i inventory/hosts.ini web1 -b -m ansible.builtin.command -a "ls -ld /opt/lab-demo"
```

```text
drwxr-xr-x ... ubuntu ... /opt/lab-demo
```

---

### Step 13 — Gather one fact ad hoc (preview Lab 02)

```bash
ansible -i inventory/hosts.ini web1 -m ansible.builtin.setup \
  -a "filter=ansible_distribution*"
```

**Validate**

JSON includes `"ansible_distribution": "Ubuntu"` and version `22.04`.

---

### Step 14 — Test appserver connectivity

```bash
ansible -i inventory/hosts.ini appservers -m ansible.builtin.ping
```

**Validate**

`app1` returns `pong`. All three inventory hosts are reachable before Lab 02.

---

## Architecture

```
┌──────────────────┐         SSH          ┌─────────────┐
│  Control Node    │ ───────────────────► │    web1     │
│  ansible -m ...  │                      │  Ubuntu 22  │
│  inventory/      │ ───────────────────► │    web2     │
│  hosts.ini       │                      └─────────────┘
│                  │ ───────────────────► ┌─────────────┐
│                  │                      │    app1     │
└──────────────────┘                      └─────────────┘
```

## Ad hoc flag reference

| Flag | Long form | Purpose |
|------|-----------|---------|
| `-i` | `--inventory` | Inventory file or script |
| `-m` | `--module-name` | Module to execute (FQCN) |
| `-a` | `--args` | Module arguments |
| `-b` | `--become` | Privilege escalation (sudo) |
| `-l` | `--limit` | Restrict to host pattern |
| `-f` | `--forks` | Parallelism (default 5) |
| `-C` | `--check` | Dry-run mode |
| `-v` | `-vvv` | Increase verbosity |

## Reflection questions

1. Why does `ansible.builtin.apt` require `-b` but `ping` does not?
2. What is the difference between `changed` and `ok` in module output?
3. When would you choose ad hoc over a playbook?
4. Why use FQCN (`ansible.builtin.ping`) instead of short name (`ping`)?

## Module reference (this lab)

| Module | Ad hoc example |
|--------|----------------|
| `ansible.builtin.ping` | Connectivity |
| `ansible.builtin.command` | Run single command |
| `ansible.builtin.apt` | Debian/Ubuntu packages |
| `ansible.builtin.service` | systemd units |
| `ansible.builtin.copy` | Push content to path |
| `ansible.builtin.user` | Local user accounts |
| `ansible.builtin.debug` | Print variables/messages |

---

## Done when

- [ ] `ansible.builtin.ping` succeeds on all `webservers`
- [ ] You installed `curl` with `ansible.builtin.apt` using `--become`
- [ ] nginx is `active` on both web hosts
- [ ] `/tmp/adhoc-marker.txt` exists with expected content
- [ ] User `labops` exists on both hosts
- [ ] You used `-l` to target a single host

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `UNREACHABLE` | Wrong IP or SSH | Test `ssh ubuntu@<ip>`; update inventory |
| `Permission denied` (apt) | Missing `--become` | Add `-b` |
| `Failed to connect to the host via ssh` | Security group | Allow port 22 from control node |
| `Using a module not fully qualified` | Short module name | Use `ansible.builtin.*` FQCN |
| `Could not find apt package` | Typo in package name | Verify spelling; run `apt search` on host |

## Cleanup

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.user -a "name=labops state=absent remove=yes"
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.file -a "path=/tmp/adhoc-marker.txt state=absent"
# Optional: remove nginx if not needed for later labs
# ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.apt -a "name=nginx state=absent autoremove=yes"
```

---
*Source: Lesson 3 AP-02 · Next: [lab02 — Facts](lab02-facts.md) · Deep dive: [gathering facts](../docs/facts/gathering-facts.md)*
