# Lab 05: Implementing Conditionals in Playbooks

> **Goal:** Branch tasks with `when`, combine fact checks, and skip work based on group membership.
> **Time:** ~45 min · **Files:** `labs/playbooks/conditionals-os.yml` · **Source:** Lesson 5 AP-04

## Before you start

- [lab04](lab04-loops.md) complete

## Concepts

`when` clauses accept Jinja2 expressions. Common patterns:

- `ansible_facts.os_family == "Debian"`
- `inventory_hostname in groups['webservers']`
- `enable_firewall | bool`

---

## Steps

### Step 1 — Review playbook

```bash
cd ~/terraform-ansible-labs/ansible/extended/labs
less playbooks/conditionals-os.yml
```

**Validate**

```bash
ansible-playbook --syntax-check playbooks/conditionals-os.yml
```

---

### Step 2 — Run against all hosts

```bash
ansible-playbook -i inventory/hosts.ini playbooks/conditionals-os.yml
```

**Validate**

`failed=0` for web1, web2, app1.

---

### Step 3 — Confirm nginx only on webservers

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.command -a "systemctl is-active nginx"
ansible -i inventory/hosts.ini appservers -b -m ansible.builtin.command -a "systemctl is-active nginx"
```

**Validate**

- webservers: `active`
- appservers: may show `inactive` or fail (nginx not installed there — expected)

---

### Step 4 — Check custom index page

```bash
ansible -i inventory/hosts.ini web1 -m ansible.builtin.uri   -a "url=http://127.0.0.1/ return_content=yes"
```

**Validate**

HTML contains hostname and `Ubuntu` / `22.04`.

---

### Step 5 — Run with firewall disabled

```bash
ansible-playbook -i inventory/hosts.ini playbooks/conditionals-os.yml -e "enable_firewall=false"
```

**Validate**

UFW task shows `skipping` in output.

---

### Step 6 — Run with firewall enabled

```bash
ansible-playbook -i inventory/hosts.ini playbooks/conditionals-os.yml -e "enable_firewall=true"
```

**Validate**

UFW allow rule task runs on Debian hosts (may require `ufw` package).

---

### Step 7 — Observe skip message on web tier

Look for debug task: `not in appservers — skipping app tasks` on web1/web2.

**Validate**

Message appears in play output for webservers.

---

### Step 8 — Test false condition manually

```bash
ansible -i inventory/hosts.ini web1 -m ansible.builtin.debug   -a "msg=skipped" -e "ansible_facts_os_family=RedHat"
```

Note: overriding facts ad hoc is limited; instead verify `when` in playbook uses live facts.

---

### Step 9 — Verbose condition tracing

```bash
ansible-playbook -i inventory/hosts.ini playbooks/conditionals-os.yml -v
```

**Validate**

Skipped tasks show `skipping: [host] => (item=...) false_condition`

---

### Step 10 — Document your branches

In your notes, list three `when` expressions from the playbook and what each gates.

**Validate**

You can explain each conditional without reading the file.

---

## Done when

- [ ] Playbook succeeds on all inventory hosts
- [ ] nginx runs on webservers only
- [ ] Index page shows OS version
- [ ] UFW task respects `enable_firewall`
- [ ] Skip debug appears on non-app hosts

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| nginx on wrong host | Group membership | Check `inventory/hosts.ini` groups |
| UFW module not found | Package missing | `apt install ufw` or skip firewall task |
| Facts undefined | gather_facts false | Ensure setup task runs |

## Cleanup

None required; nginx may be reused in lab06.

---
*Source: Lesson 5 AP-04 · Next: [lab06](lab06-handlers.md) · Deep dive: [conditionals](../docs/playbooks/loops-and-conditionals.md)*
