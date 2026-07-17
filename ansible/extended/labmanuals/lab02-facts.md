# Lab 02: Working with Ansible Facts

> **Goal:** Gather, filter, and use host facts in ad hoc commands and debug output; deploy custom local facts.
> **Time:** ~45 min · **Files:** `labs/inventory/hosts.ini` · **Source:** Lesson 3 AP-03

## Before you start

- [lab01](lab01-adhoc-modules.md) complete
- Control node can reach all hosts in inventory

## Concepts

Facts are variables Ansible discovers about each host: OS, memory, network, mounts, and more. The `setup` module collects them (runs automatically at play start unless disabled).

| Variable prefix | Source |
|-----------------|--------|
| `ansible_*` | Default facts from `setup` |
| `ansible_local.*` | Custom facts in `/etc/ansible/facts.d/` |

---

## Steps

### Step 1 — Gather all facts (verbose)

```bash
cd ~/terraform-ansible-labs/ansible/extended/labs
ansible -i inventory/hosts.ini web1 -m ansible.builtin.setup
```

**Validate**

JSON output includes keys like `ansible_distribution`, `ansible_memtotal_mb`, `ansible_default_ipv4`.

---

### Step 2 — Filter facts with `filter`

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

### Step 3 — Memory and CPU subset

```bash
ansible -i inventory/hosts.ini webservers -m ansible.builtin.setup \
  -a "filter=ansible_processor*"
```

**Validate**

Output includes `ansible_processor_vcpus` (integer ≥ 1).

---

### Step 4 — Print facts with debug (ad hoc)

```bash
ansible -i inventory/hosts.ini webservers -m ansible.builtin.setup -a "filter=ansible_hostname"
ansible -i inventory/hosts.ini webservers -m ansible.builtin.debug \
  -a "var=hostvars[inventory_hostname]['ansible_hostname']"
```

**Validate**

Each host shows its inventory name matching `ansible_hostname` or expected hostname.

---

### Step 5 — Compare OS family across groups

```bash
ansible -i inventory/hosts.ini all -m ansible.builtin.setup -a "filter=ansible_os_family"
ansible -i inventory/hosts.ini all -m ansible.builtin.debug \
  -a "msg={{ inventory_hostname }} runs {{ ansible_os_family }}"
```

**Validate**

```text
"msg": "web1 runs Debian"
```

Ubuntu reports `Debian` family (expected on 22.04).

---

### Step 6 — Network facts

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

Address should match your VPC private IP.

---

### Step 7 — Deploy custom local facts

Create a fact file on all webservers:

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.copy -a 'dest=/etc/ansible/facts.d/lab.fact mode=0755 content="[lab]\ntier=web\ncourse=extended\n"'
```

**Validate**

```bash
ansible -i inventory/hosts.ini web1 -b -m ansible.builtin.command -a "cat /etc/ansible/facts.d/lab.fact"
```

```ini
[lab]
tier=web
course=extended
```

---

### Step 8 — Re-gather and read `ansible_local`

```bash
ansible -i inventory/hosts.ini webservers -m ansible.builtin.setup
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

---

### Step 9 — Fact caching awareness (read-only)

Facts are refreshed each play unless fact caching is configured in `ansible.cfg`. For this lab, no cache is enabled.

```bash
grep -i fact_caching ansible.cfg || echo "No fact caching configured (expected)"
```

**Validate**

No `fact_caching` line, or it is commented out.

---

### Step 10 — Selective gather in a one-line playbook

```bash
ansible -i inventory/hosts.ini webservers -m ansible.builtin.setup \
  -a "gather_subset=!all,distribution,network"
```

**Validate**

Output is smaller than full fact dump but still includes `ansible_distribution` and network interfaces.

---

## Done when

- [ ] You filtered facts with `filter=`
- [ ] `ansible_os_family` is `Debian` on Ubuntu 22.04 hosts
- [ ] Custom fact `/etc/ansible/facts.d/lab.fact` exists
- [ ] `ansible_local.lab.tier` equals `web`

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `ansible_local` undefined | Facts not re-gathered | Run `setup` again after deploying `.fact` file |
| Empty filter results | Wrong pattern | Use `ansible_distribution*` with asterisk |
| Permission denied on facts.d | Missing become | Add `-b` to copy task |
| Python errors on setup | Wrong interpreter | Set `ansible_python_interpreter=/usr/bin/python3` in inventory |

## Cleanup

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.file \
  -a "path=/etc/ansible/facts.d/lab.fact state=absent"
```

---
*Source: Lesson 3 AP-03 · Next: [lab03](lab03-nodejs-playbook.md) · Deep dive: [custom facts](../docs/facts/custom-facts.md)*
