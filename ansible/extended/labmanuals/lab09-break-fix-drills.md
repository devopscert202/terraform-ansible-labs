# Lab 09: Break-Fix Drills

> **Goal:** Diagnose and repair common Ansible failures — YAML syntax, privilege escalation, handler names, FQCN modules, and inventory variables.
> **Time:** ~45 min · **Files:** `labs/break-fix/` · **Source:** New (synthesis lab)

## Before you start

- [lab08](lab08-roles-project.md) complete
- Comfortable reading Ansible error messages

## How this lab works

Each drill ships a **broken** file. Your job:

1. Run it and capture the error
2. Identify root cause
3. Fix it (or compare to `solutions/`)
4. Verify success

Do not peek at solutions until you have attempted a fix.

---

## Drill 01 — YAML indentation

### Step 1 — Run broken playbook

```bash
cd ~/terraform-ansible-labs/ansible/extended/labs
ansible-playbook -i inventory/hosts.ini break-fix/drill-01-broken-yaml.yml
```

**Validate (expected failure)**

```text
ERROR! We were unable to read ...
```

Or YAML parser error pointing to line with bad indent.

### Step 2 — Fix and verify

Align `ansible.builtin.apt` with `name:` under `tasks`.

```bash
ansible-playbook -i inventory/hosts.ini break-fix/solutions/drill-01-fixed.yml
```

**Validate**

```text
failed=0
```

---

## Drill 02 — Missing become

### Step 1 — Run

```bash
ansible-playbook -i inventory/hosts.ini break-fix/drill-02-missing-become.yml
```

**Validate (expected failure)**

Permission denied installing packages as unprivileged user.

### Step 2 — Fix

Add `become: true` at play level (see solution).

```bash
ansible-playbook -i inventory/hosts.ini break-fix/solutions/drill-02-fixed.yml
```

**Validate**

`failed=0`

---

## Drill 03 — Handler name mismatch

### Step 1 — Run broken playbook twice

```bash
ansible-playbook -i inventory/hosts.ini break-fix/drill-03-handler-mismatch.yml
```

**Validate**

Play may succeed but handler **never runs** — `notify: restart nginx` ≠ `Restart nginx`.

### Step 2 — Confirm nginx not restarted

Check playbook output for missing `RUNNING HANDLER`.

### Step 3 — Fix notify string

```bash
ansible-playbook -i inventory/hosts.ini break-fix/solutions/drill-03-fixed.yml
```

**Validate**

`RUNNING HANDLER [Restart nginx]` appears when config changes.

---

## Drill 04 — Non-FQCN module

### Step 1 — Run

```bash
ansible-playbook -i inventory/hosts.ini break-fix/drill-04-non-fqcn.yml
```

**Validate**

May work with warning, or fail depending on Ansible version/config.

### Step 2 — Fix to FQCN

```bash
ansible-playbook -i inventory/hosts.ini break-fix/solutions/drill-04-fixed.yml
```

**Validate**

`ansible.builtin.ping` succeeds without deprecation warning.

---

## Drill 05 — Wrong Python interpreter

### Step 1 — Ping with broken inventory

```bash
ansible -i break-fix/drill-05-broken-inventory.ini webservers -m ansible.builtin.ping
```

**Validate (expected failure)**

Python 2 path not found or module failure.

### Step 2 — Fix inventory

```bash
ansible -i break-fix/solutions/drill-05-fixed-inventory.ini webservers -m ansible.builtin.ping
```

**Validate**

```text
"pong"
```

---

## Drill 06 — Speed run (optional)

Fix all five drills without solutions in under 30 minutes.

**Validate**

All solution playbooks/inventory pass.

---

## Troubleshooting patterns

| Error type | First check |
|------------|-------------|
| YAML | `ansible-playbook --syntax-check` |
| Permission | `become: true` / `-b` |
| Handler | Exact `notify` name match |
| Module | FQCN `ansible.builtin.*` |
| Connection | Inventory IP and `ansible_user` |

---

## Done when

- [ ] Fixed YAML indentation drill
- [ ] Fixed missing become drill
- [ ] Fixed handler mismatch drill
- [ ] Converted short module to FQCN
- [ ] Fixed Python interpreter in inventory
- [ ] Documented one error message and root cause in your notes

## Error message reference

| Drill | Typical error fragment | Root cause |
|-------|------------------------|------------|
| 01 | `could not find expected ':'` | YAML indent under task list |
| 02 | `Permission denied` / `E: Could not open lock file` | Missing `become: true` |
| 03 | (no error — silent skip) | `notify` string ≠ handler `name` |
| 04 | `[DEPRECATION WARNING]` or `couldn't resolve module/action 'ping'` | Short module name instead of FQCN |
| 05 | `/usr/bin/python: No such file` | Python 2 interpreter on Ubuntu 22.04 |

Copy one full error from your terminal into your notes with the fix you applied.

---

## Cleanup

No resources created on targets beyond optional nginx from drill 02/03.

---
*Source: Synthesis · Track complete · Return to [README](README.md) · Deep dive: [break-fix](../html/break-fix.html)*
