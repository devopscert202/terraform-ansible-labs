# Lab 02: Working with Ansible Facts

> **Goal:** Gather, filter, and use host facts in ad hoc commands and debug output; deploy custom local facts.
> **Time:** ~45 min · **Files:** `labs/inventory/hosts.ini` · **Source:** Lesson 3 AP-03
> **Interactive:** [facts.html](../html/facts.html)

## Before you start

- [lab01](lab01-adhoc-modules.md) complete — all hosts return `pong`
- Control node can reach all hosts in inventory
- Review [gathering-facts.md](../docs/facts/gathering-facts.md) (10 min read)

## Concepts

Facts are variables Ansible discovers about each host: OS, memory, network, mounts, and more. The `setup` module collects them (runs automatically at play start unless disabled).

| Variable prefix | Source |
|-----------------|--------|
| `ansible_*` | Default facts from `setup` |
| `ansible_local.*` | Custom facts in `/etc/ansible/facts.d/` |

| Key fact | Ubuntu 22.04 example | Common use |
|----------|---------------------|------------|
| `ansible_distribution` | Ubuntu | Display, logging |
| `ansible_os_family` | Debian | Package manager `when` |
| `ansible_memtotal_mb` | 976 | Capacity checks |
| `ansible_default_ipv4.address` | 10.0.x.x | Bind address |

---

## Part A — Gathering facts ad hoc

### Step 1 — Enter lab directory and confirm inventory

```bash
cd ~/terraform-ansible-labs/ansible/extended/labs
ansible-inventory -i inventory/hosts.ini --graph
```

**Validate**

```text
@webservers:
  |--web1
  |--web2
@appservers:
  |--app1
```

Three hosts across two groups.

---

### Step 2 — Gather all facts on one host (verbose)

```bash
ansible -i inventory/hosts.ini web1 -m ansible.builtin.setup 2>/dev/null | head -50
```

**Validate**

JSON output includes keys like `ansible_distribution`, `ansible_memtotal_mb`, `ansible_default_ipv4`.

**Note:** Full output is large (200KB+). Use filters in production.

---

### Step 3 — Filter facts with glob pattern

```bash
ansible -i inventory/hosts.ini webservers -m ansible.builtin.setup \
  -a "filter=ansible_distribution*"
```

**Validate**

```text
"ansible_distribution": "Ubuntu",
"ansible_distribution_version": "22.04",
"ansible_distribution_release": "jammy",
```

Only distribution-related keys appear.

---

### Step 4 — Memory and CPU subset

```bash
ansible -i inventory/hosts.ini webservers -m ansible.builtin.setup \
  -a "filter=ansible_processor*"
```

**Validate**

Output includes `ansible_processor_vcpus` (integer ≥ 1).

```bash
ansible -i inventory/hosts.ini web1 -m ansible.builtin.setup \
  -a "filter=ansible_memtotal_mb"
```

`ansible_memtotal_mb` is a positive integer.

---

### Step 5 — Print facts with debug module

```bash
ansible -i inventory/hosts.ini webservers -m ansible.builtin.setup \
  -a "filter=ansible_hostname"
ansible -i inventory/hosts.ini webservers -m ansible.builtin.debug \
  -a "var=hostvars[inventory_hostname]['ansible_hostname']"
```

**Validate**

Each host shows hostname matching inventory name or system hostname.

---

### Step 6 — Compare OS family across all groups

```bash
ansible -i inventory/hosts.ini all -m ansible.builtin.setup \
  -a "filter=ansible_os_family"
ansible -i inventory/hosts.ini all -m ansible.builtin.debug \
  -a "msg={{ inventory_hostname }} runs {{ ansible_os_family }}"
```

**Validate**

```text
"msg": "web1 runs Debian"
"msg": "app1 runs Debian"
```

Ubuntu reports `Debian` family — **expected**, not an error.

---

### Step 7 — Network facts for one host

```bash
ansible -i inventory/hosts.ini web1 -m ansible.builtin.setup \
  -a "filter=ansible_default_ipv4"
```

**Validate**

```json
"ansible_default_ipv4": {
    "address": "10.0.x.x",
    "gateway": "...",
    "interface": "ens5"
}
```

Address should match your VPC private IP for `web1`.

---

## Part B — Custom local facts

### Step 8 — Verify facts.d directory (optional)

```bash
ansible -i inventory/hosts.ini web1 -b -m ansible.builtin.file \
  -a "path=/etc/ansible/facts.d state=directory mode=0755"
```

**Validate**

```text
"changed": false
```
or `changed: true` if directory was created.

---

### Step 9 — Deploy custom fact file to webservers

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.copy \
  -a 'dest=/etc/ansible/facts.d/lab.fact mode=0755 content="[lab]\ntier=web\ncourse=extended\n"'
```

**Validate**

```bash
ansible -i inventory/hosts.ini web1 -b -m ansible.builtin.command \
  -a "cat /etc/ansible/facts.d/lab.fact"
```

```ini
[lab]
tier=web
course=extended
```

---

### Step 10 — Re-gather facts after custom fact deploy

```bash
ansible -i inventory/hosts.ini webservers -m ansible.builtin.setup
```

**Validate**

Setup completes with `changed: false` on all hosts (fact gather always runs module).

---

### Step 11 — Read ansible_local variables

```bash
ansible -i inventory/hosts.ini webservers -m ansible.builtin.debug \
  -a "var=ansible_local.lab"
```

**Validate**

```json
"ansible_local": {
    "lab": {
        "tier": "web",
        "course": "extended"
    }
}
```

If undefined — re-run Step 10.

---

### Step 12 — Use custom fact in debug message

```bash
ansible -i inventory/hosts.ini webservers -m ansible.builtin.debug \
  -a "msg=Host {{ inventory_hostname }} is tier {{ ansible_local.lab.tier }}"
```

**Validate**

Each webserver prints `tier web`.

---

## Part C — Advanced fact gathering

### Step 13 — Selective gather_subset

```bash
ansible -i inventory/hosts.ini webservers -m ansible.builtin.setup \
  -a "gather_subset=!all,distribution,network"
```

**Validate**

Output is smaller than full dump but includes `ansible_distribution` and network interfaces.

---

### Step 14 — Fact caching awareness

```bash
grep -i fact_caching ansible.cfg || echo "No fact caching configured (expected)"
```

**Validate**

No active `fact_caching` line — facts refresh each play in this lab.

---

### Step 15 — Python version fact

```bash
ansible -i inventory/hosts.ini all -m ansible.builtin.setup \
  -a "filter=ansible_python*"
```

**Validate**

`ansible_python_version` shows 3.x (e.g., 3.10.12). Confirms interpreter for modules.

---

## Part D — Documentation exercise

### Step 16 — Record three facts for your environment

In your notes, document actual values from your lab:

| Host | distribution | memtotal_mb | default_ipv4 |
|------|-------------|-------------|--------------|
| web1 | | | |
| web2 | | | |
| app1 | | | |

**Validate**

Table completed with values from Steps 3 and 7.

---

## Done when

- [ ] You filtered facts with `filter=ansible_distribution*`
- [ ] `ansible_os_family` is `Debian` on Ubuntu 22.04 hosts
- [ ] Custom fact `/etc/ansible/facts.d/lab.fact` exists on webservers
- [ ] `ansible_local.lab.tier` equals `web`
- [ ] You used `gather_subset` for selective gather
- [ ] You can explain fact gathering pipeline (play → setup → ansible_facts)

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `ansible_local` undefined | Facts not re-gathered | Run `setup` after deploying `.fact` |
| Empty filter results | Wrong pattern | Use `ansible_distribution*` with asterisk |
| Permission denied on facts.d | Missing become | Add `-b` to copy task |
| Python errors on setup | Wrong interpreter | `ansible_python_interpreter=/usr/bin/python3` in inventory |
| `UNREACHABLE` | SSH issue | Return to lab01 connectivity steps |

## Cleanup

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.file \
  -a "path=/etc/ansible/facts.d/lab.fact state=absent"
```

## Knowledge check

1. What module collects facts?
2. Where do custom facts appear in the variable namespace?
3. Why does Ubuntu report `os_family: Debian`?
4. When would you set `gather_facts: false`?

---
*Source: Lesson 3 AP-03 · Next: [lab03](lab03-nodejs-playbook.md) · Deep dive: [custom facts](../docs/facts/custom-facts.md) · Interactive: [facts.html](../html/facts.html)*
