# Lab 04: Apache Playbook

> **Goal:** Apache runs on all web servers; config changes trigger a handler restart.
> **Time:** ~75 min · **Files:** `labs/playbooks/apache.yml`

## Before you start

- [lab03](lab03-adhoc-commands.md) complete

## Steps

### Step 1 — Review the playbook

```bash
cd ~/terraform-ansible-labs/ansible/essentials/labs
less playbooks/apache.yml
```

Tasks install `apache2` and enable `mod_rewrite`. The handler restarts Apache when that module changes.

### Step 2 — Apply the playbook

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/apache.yml
```

**Validate**

```text
PLAY RECAP *********************************************************************
web1   : ok=...   changed=...   unreachable=0   failed=0
web2   : ok=...   changed=...   unreachable=0   failed=0
```

`failed=0` on every host.

### Step 3 — Confirm the service

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.command -a "systemctl is-active apache2"
```

**Validate**

```text
active
```

on each host.

### Step 4 — Re-run (idempotency)

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/apache.yml
```

**Validate** — Second run shows `changed=0` for install tasks (handler may still run if notified).

## Done when

- [ ] Playbook completes with `failed=0`
- [ ] `apache2` is `active`
- [ ] Second run is mostly `ok` / `changed=0`

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `Permission denied` | Missing privilege escalation | Playbook uses `become: true`; check sudo |
| `Failed to lock apt` | Another apt process | Wait and retry |

## Cleanup

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.apt -a "name=apache2 state=absent purge=true"
```

---
*Source: Lesson 4 AP-01 · Next: [lab05](lab05-playbook-variables.md) · Deep dive: [playbook doc](../docs/04-playbooks/playbook-and-yaml-basics.md)*
