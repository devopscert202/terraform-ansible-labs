# Lab 03: Ad Hoc Commands

> **Goal:** Run one-off commands on multiple hosts without writing a playbook.
> **Time:** ~45 min · **Files:** none (commands only)

## Before you start

- [lab02](lab02-inventory-hosts-groups.md) complete
- Inventory: `labs/inventory/hosts.ini.local` (or `hosts.yaml`)

## Steps

### Step 1 — Check uptime on all web servers

```bash
cd ~/terraform-ansible-labs/ansible/essentials/labs
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.command -a "uptime"
```

**Validate**

```text
web1 | CHANGED | rc=0 >>
 web1 |  ... up ...
web2 | CHANGED | rc=0 >>
```

`rc=0` on each host.

### Step 2 — Install a package on one host

```bash
ansible web1 -i inventory/hosts.ini.local -b -m ansible.builtin.apt -a "name=tree state=present update_cache=yes"
```

**Validate**

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.command -a "which tree"
```

```text
/usr/bin/tree
```

### Step 3 — Gather facts (optional preview)

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.setup -a "filter=ansible_distribution*"
```

**Validate** — JSON shows `"ansible_distribution": "Ubuntu"`.

## Done when

- [ ] You ran ad hoc commands on one host and a group
- [ ] `-b` used when the task needs root (package install)

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `sudo: a password is required` | Missing become | Add `-b` or configure NOPASSWD sudo |
| `Could not find apt` | Wrong OS family | Confirm Ubuntu targets |

## Cleanup

```bash
ansible web1 -i inventory/hosts.ini.local -b -m ansible.builtin.apt -a "name=tree state=absent"
```

---
*Source: Lesson 3 AP-01 · Next: [lab04](lab04-playbook-apache-webserver.md) · Deep dive: [ad hoc doc](../docs/03-adhoc/adhoc-commands.md)*
