# Lab 05: Implementing Conditionals in Playbooks

> **Goal:** Branch tasks with `when`, combine fact checks, and skip work based on group membership.
> **Time:** ~45 min · **Files:** `labs/playbooks/conditionals-os.yml` · **Source:** Lesson 5 AP-04
> **Interactive:** [loops-conditionals.html](../html/loops-conditionals.html)

## Before you start

- [lab04](lab04-loops.md) complete
- nginx may or may not be installed from prior labs — playbook installs it
- Review `when` section in [loops-and-conditionals.md](../docs/playbooks/loops-and-conditionals.md)

## Concepts

`when` clauses accept Jinja2 expressions. Ansible skips tasks when condition evaluates false.

| Pattern | Example |
|---------|---------|
| OS family | `ansible_facts.os_family == "Debian"` |
| Group membership | `inventory_hostname in groups['webservers']` |
| Boolean flag | `enable_firewall | bool` |
| Multiple AND | YAML list of conditions |

---

## Part A — Playbook review

### Step 1 — Review conditionals-os.yml

```bash
cd ~/terraform-ansible-labs/ansible/extended/labs
less playbooks/conditionals-os.yml
```

Note tasks gated by:
- `ansible_facts.os_family`
- `inventory_hostname in groups[...]`
- `enable_firewall | bool`

**Validate**

```bash
ansible-playbook --syntax-check playbooks/conditionals-os.yml
```

No syntax errors.

---

### Step 2 — List tasks and hosts

```bash
ansible-playbook -i inventory/hosts.ini playbooks/conditionals-os.yml --list-tasks
ansible-playbook -i inventory/hosts.ini playbooks/conditionals-os.yml --list-hosts
```

**Validate**

Hosts: web1, web2, app1. Multiple tasks with implied `when` (visible in file).

---

## Part B — Execute against all hosts

### Step 3 — First full run

```bash
ansible-playbook -i inventory/hosts.ini playbooks/conditionals-os.yml
```

**Validate**

```text
PLAY RECAP *********************************************************************
web1   : failed=0
web2   : failed=0
app1   : failed=0
```

---

### Step 4 — Confirm nginx on webservers only

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.command   -a "systemctl is-active nginx"
```

**Validate**

```text
active
active
```

```bash
ansible -i inventory/hosts.ini appservers -b -m ansible.builtin.command   -a "systemctl is-active nginx" 2>&1 || true
```

**Validate**

`inactive` or command failure on app1 — **expected** (nginx not installed on app tier).

---

### Step 5 — Check custom index page on web1

```bash
ansible -i inventory/hosts.ini web1 -m ansible.builtin.uri   -a "url=http://127.0.0.1/ return_content=yes"
```

**Validate**

HTML content includes hostname and references to `Ubuntu` / `22.04`.

---

### Step 6 — Verify app tier skip message

Re-read playbook output from Step 3 or re-run with `-v`:

```bash
ansible-playbook -i inventory/hosts.ini playbooks/conditionals-os.yml 2>&1 | grep -i "skipping"
```

**Validate**

Web hosts show skip message for app-only tasks. App host skips web-only tasks.

---

## Part C — Firewall flag exercises

### Step 7 — Run with firewall disabled

```bash
ansible-playbook -i inventory/hosts.ini playbooks/conditionals-os.yml   -e "enable_firewall=false"
```

**Validate**

UFW-related tasks show `skipping` in output.

---

### Step 8 — Run with firewall enabled

```bash
ansible-playbook -i inventory/hosts.ini playbooks/conditionals-os.yml   -e "enable_firewall=true"
```

**Validate**

UFW allow rule task runs on Debian hosts. May require `ufw` package (playbook may install it).

```bash
ansible -i inventory/hosts.ini web1 -b -m ansible.builtin.command   -a "ufw status" 2>&1 || echo "ufw not installed — check playbook"
```

---

## Part D — Debugging conditionals

### Step 9 — Verbose condition tracing

```bash
ansible-playbook -i inventory/hosts.ini playbooks/conditionals-os.yml -v 2>&1 | head -80
```

**Validate**

Skipped tasks show `false_condition` or `skipping:` in verbose output.

---

### Step 10 — Document three when expressions

In your notes, copy three `when` clauses from the playbook and explain what each gates.

| # | when expression | What it controls |
|---|-----------------|------------------|
| 1 | | |
| 2 | | |
| 3 | | |

**Validate**

You can explain each without reading the file.

---

### Step 11 — Test os_family fact ad hoc

```bash
ansible -i inventory/hosts.ini all -m ansible.builtin.setup   -a "filter=ansible_os_family"
ansible -i inventory/hosts.ini all -m ansible.builtin.debug   -a "msg=os_family={{ ansible_os_family }}"
```

**Validate**

All Ubuntu hosts report `Debian`.

---

### Step 12 — Limit to webservers

```bash
ansible-playbook -i inventory/hosts.ini playbooks/conditionals-os.yml --limit webservers
```

**Validate**

`app1` not in recap.

---

## Part E — Reflection

### Step 13 — Loop vs when

Answer in notes: Why does lab04 use `loop` but lab05 uses `when`?

**Validate**

Loop = repeat same task. When = include/skip entire task.

---



## Part F — Additional conditional patterns

### Step 14 — Compare web vs app index behavior

```bash
ansible -i inventory/hosts.ini web1 -m ansible.builtin.uri   -a "url=http://127.0.0.1/ return_content=yes status_code=200"
ansible -i inventory/hosts.ini app1 -m ansible.builtin.uri   -a "url=http://127.0.0.1/ return_content=yes status_code=200" 2>&1 || echo "Expected: no nginx on app1"
```

**Validate**

Web1 returns HTML. App1 may fail or show default — confirms tier separation.

---

### Step 15 — Extra var type coercion

```bash
ansible-playbook -i inventory/hosts.ini playbooks/conditionals-os.yml   -e "enable_firewall=yes" -v 2>&1 | grep -i ufw | head -5
```

**Validate**

String `yes` coerced to true via `| bool` filter in when clause.

---

### Step 16 — Dry-run conditionals

```bash
ansible-playbook -i inventory/hosts.ini playbooks/conditionals-os.yml --check
```

**Validate**

Play completes; skipped tasks still show as skipping even in check mode.

---

### Step 17 — Facts required for conditionals

```bash
grep gather_facts playbooks/conditionals-os.yml || echo "gather_facts defaults to true"
ansible -i inventory/hosts.ini web1 -m ansible.builtin.setup -a "filter=ansible_distribution*"
```

**Validate**

Distribution facts available for template conditionals.

---

### Step 18 — Inventory group verification

```bash
ansible-inventory -i inventory/hosts.ini --graph
ansible -i inventory/hosts.ini web1 -m ansible.builtin.debug -a "var=group_names"
```

**Validate**

`web1` group_names includes `webservers`. `app1` includes `appservers`.

---

## Architecture note

```
conditionals-os.yml
├── All hosts: common tasks (facts, debug)
├── when Debian: apt-based tasks
├── when webservers: nginx + index template
├── when appservers: app-specific tasks (skipped on web)
└── when enable_firewall: UFW rules
```

## Knowledge check

1. Why use `ansible_facts.os_family` instead of `ansible_distribution` for apt tasks?
2. How do you skip a task for one tier only?
3. What happens when all `when` list items must be true?
4. How does `-e enable_firewall=false` reach the playbook?


## Done when

- [ ] Playbook succeeds on web1, web2, app1
- [ ] nginx active on webservers only
- [ ] Index page shows OS version on web tier
- [ ] UFW task respects `enable_firewall` extra var
- [ ] Skip messages visible for tier-specific tasks
- [ ] Three `when` expressions documented

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| nginx on wrong host | Group membership | Check `inventory/hosts.ini` |
| UFW module not found | Package missing | `apt install ufw` or skip task |
| Facts undefined | gather_facts false | Ensure play gathers facts |
| Template error | Missing facts in template | Run setup first |

## Cleanup

None required; nginx reused in lab06.

---
*Source: Lesson 5 AP-04 · Next: [lab06](lab06-handlers.md) · Deep dive: [conditionals](../docs/playbooks/loops-and-conditionals.md)*
