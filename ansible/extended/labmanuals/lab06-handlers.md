# Lab 06: Configuring Tasks with Handlers

> **Goal:** Use `notify`, `handlers`, and `meta: flush_handlers` to reload nginx only when configuration changes.
> **Time:** ~45 min · **Files:** `labs/playbooks/handlers-nginx.yml` · **Source:** Lesson 5 AP-05

## Before you start

- [lab05](lab05-conditionals.md) complete
- nginx may already be installed from prior labs

## Concepts

Handlers are tasks that run **once at end of play** if notified. Names must match exactly.

---

## Steps

### Step 1 — Review playbook and template

```bash
cd ~/terraform-ansible-labs/ansible/extended/labs
less playbooks/handlers-nginx.yml
cat playbooks/templates/nginx-lab.conf.j2
```

**Validate**

```bash
ansible-playbook --syntax-check playbooks/handlers-nginx.yml
```

---

### Step 2 — First run

```bash
ansible-playbook -i inventory/hosts.ini playbooks/handlers-nginx.yml
```

**Validate**

Handler `Reload nginx` runs (look for `RUNNING HANDLER`).

---

### Step 3 — Second run (idempotent)

```bash
ansible-playbook -i inventory/hosts.ini playbooks/handlers-nginx.yml
```

**Validate**

No handler execution (`RUNNING HANDLER` absent) when config unchanged.

---

### Step 4 — Verify site enabled

```bash
ansible -i inventory/hosts.ini web1 -b -m ansible.builtin.command   -a "ls -l /etc/nginx/sites-enabled/lab.conf"
```

**Validate**

Symlink to `sites-available/lab.conf`.

---

### Step 5 — HTTP check from playbook

Playbook includes `uri` task to localhost. Re-run and confirm debug shows HTML snippet.

**Validate**

```text
"msg": "<!DOCTYPE html>..."
```

---

### Step 6 — Force config change

Edit `playbooks/templates/nginx-lab.conf.j2` — add comment `# lab change` — then run playbook.

**Validate**

Template task `changed`, handler `Reload nginx` runs.

---

### Step 7 — Test handler name mismatch (break awareness)

Read `break-fix/drill-03-handler-mismatch.yml` and predict behavior.

**Validate**

You understand notify `restart nginx` ≠ handler `Restart nginx`.

---

### Step 8 — flush_handlers

Note playbook task `meta: flush_handlers` before URI check.

**Validate**

nginx reloaded before HTTP test even mid-play.

---

### Step 9 — Validate nginx config syntax

Template uses `validate: nginx -t`. Intentionally break template locally, run playbook, observe failure.

**Validate**

Task fails before deploying bad config (restore template after).

---

### Step 10 — Service state

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.service_facts
ansible -i inventory/hosts.ini webservers -m ansible.builtin.debug   -a "var=ansible_facts.services['nginx.service'].state"
```

**Validate**

`running` on webservers.

---

## Done when

- [ ] Handler runs on first deploy
- [ ] Handler skipped when nothing changed
- [ ] `lab.conf` site is enabled
- [ ] HTTP returns content
- [ ] Config change triggers reload
- [ ] You understand notify/handler name matching

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Handler never runs | Name mismatch or task not changed | Check `notify` string |
| nginx fails to reload | Syntax error | Run `nginx -t` on host |
| default site still active | File task order | Re-run playbook |

## Cleanup

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.file   -a "path=/etc/nginx/sites-enabled/lab.conf state=absent"
```

---
*Source: Lesson 5 AP-05 · Next: [lab07](lab07-dynamic-inventory.md) · Deep dive: [handlers](../docs/playbooks/handlers-notify.md)*
