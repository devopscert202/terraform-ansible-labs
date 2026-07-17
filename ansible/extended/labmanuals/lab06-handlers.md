# Lab 06: Configuring Tasks with Handlers

> **Goal:** Use `notify`, `handlers`, and `meta: flush_handlers` to reload nginx only when configuration changes.
> **Time:** ~45 min · **Files:** `labs/playbooks/handlers-nginx.yml`, `labs/playbooks/templates/nginx-lab.conf.j2` · **Source:** Lesson 5 AP-05

## Before you start

- [lab05](lab05-conditionals.md) complete
- nginx installed on webservers (from lab05 or lab01)
- Read [handlers-notify.md](../docs/playbooks/handlers-notify.md)

## Concepts

Handlers are tasks that run **once at end of play** if notified. Critical rules:

1. Handler `name` must **exactly** match `notify` string
2. Handlers run only when notifying task reports `changed`
3. `meta: flush_handlers` runs handlers immediately mid-play

---

## Part A — Review playbook structure

### Step 1 — Enter lab directory

```bash
cd ~/terraform-ansible-labs/ansible/extended/labs
```

---

### Step 2 — Review handlers-nginx.yml

```bash
less playbooks/handlers-nginx.yml
```

Identify:
- Tasks with `notify: Reload nginx`
- `handlers:` section at play bottom
- `meta: flush_handlers` before URI check

**Validate**

```bash
ansible-playbook --syntax-check playbooks/handlers-nginx.yml
```

---

### Step 3 — Review nginx template

```bash
cat playbooks/templates/nginx-lab.conf.j2
```

**Validate**

Jinja2 variables reference `inventory_hostname` or similar.

---

### Step 4 — List handlers

```bash
grep -A5 "^  handlers:" playbooks/handlers-nginx.yml
```

**Validate**

Handler named `Reload nginx` with `state: reloaded`.

---

## Part B — First deployment

### Step 5 — First playbook run

```bash
ansible-playbook -i inventory/hosts.ini playbooks/handlers-nginx.yml
```

**Validate**

Look for:

```text
RUNNING HANDLER [Reload nginx]
```

Template or file tasks show `changed`. Handler executes after tasks complete.

---

### Step 6 — Verify site enabled

```bash
ansible -i inventory/hosts.ini web1 -b -m ansible.builtin.command   -a "ls -l /etc/nginx/sites-enabled/lab.conf"
```

**Validate**

Symlink pointing to `sites-available/lab.conf`.

---

### Step 7 — HTTP check via ad hoc

```bash
ansible -i inventory/hosts.ini web1 -m ansible.builtin.uri   -a "url=http://127.0.0.1/ return_content=yes status_code=200"
```

**Validate**

HTTP 200 with HTML content.

---

### Step 8 — nginx service state

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.command   -a "systemctl is-active nginx"
```

**Validate**

`active` on both webservers.

---

## Part C — Idempotency and handler skip

### Step 9 — Second run — no handler

```bash
ansible-playbook -i inventory/hosts.ini playbooks/handlers-nginx.yml 2>&1 | tee /tmp/lab06-run2.txt
grep "RUNNING HANDLER" /tmp/lab06-run2.txt || echo "No handlers (CORRECT)"
```

**Validate**

No `RUNNING HANDLER` line — config unchanged, handler not triggered.

---

### Step 10 — Confirm all tasks ok/changed=0

```bash
grep "PLAY RECAP" -A1 /tmp/lab06-run2.txt
```

**Validate**

`changed=0` or minimal on webservers.

---

## Part D — Trigger handler with change

### Step 11 — Modify template

Add a comment to `playbooks/templates/nginx-lab.conf.j2`:

```jinja2
# lab change - handler test
```

**Validate**

```bash
head -3 playbooks/templates/nginx-lab.conf.j2
```

Shows new comment line.

---

### Step 12 — Run playbook after template change

```bash
ansible-playbook -i inventory/hosts.ini playbooks/handlers-nginx.yml
```

**Validate**

- Template task: `changed`
- `RUNNING HANDLER [Reload nginx]` appears

---

### Step 13 — Verify nginx still serving

```bash
ansible -i inventory/hosts.ini web1 -m ansible.builtin.uri   -a "url=http://127.0.0.1/ status_code=200"
```

**Validate**

Still returns 200 after reload.

---

## Part E — Handler mismatch awareness

### Step 14 — Read break-fix drill 03

```bash
cat break-fix/drill-03-handler-mismatch.yml
```

**Validate**

You can predict: `notify: restart nginx` will NOT match `Restart nginx` handler.

---

### Step 15 — Compare with working playbook

```bash
grep notify playbooks/handlers-nginx.yml
grep "name:" playbooks/handlers-nginx.yml | grep -i reload
```

**Validate**

Exact match: `Reload nginx` / `Reload nginx`.

---

## Part F — flush_handlers and validate

### Step 16 — Locate flush_handlers in playbook

```bash
grep -B2 -A2 "flush_handlers" playbooks/handlers-nginx.yml
```

**Validate**

`meta: flush_handlers` appears before URI verification task.

---

### Step 17 — nginx config syntax on host

```bash
ansible -i inventory/hosts.ini web1 -b -m ansible.builtin.command   -a "nginx -t"
```

**Validate**

```text
syntax is ok
test is successful
```

---

### Step 18 — Service facts

```bash
ansible -i inventory/hosts.ini webservers -m ansible.builtin.service_facts
ansible -i inventory/hosts.ini web1 -m ansible.builtin.debug   -a "var=ansible_facts.services['nginx.service'].state"
```

**Validate**

`running`

---

### Step 19 — Intentional template break (optional)

Temporarily insert invalid nginx directive, run playbook, observe `validate:` failure. **Restore template after.**

**Validate**

Task fails before deploying broken config.

---

### Step 20 — Revert template comment

Remove test comment from `nginx-lab.conf.j2` to clean state.

---

## Done when

- [ ] Handler runs on first deploy
- [ ] Handler skipped when nothing changed
- [ ] `lab.conf` site enabled via symlink
- [ ] HTTP returns 200
- [ ] Template change triggers reload
- [ ] You understand notify/handler name matching
- [ ] You located `flush_handlers` in playbook

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Handler never runs | Name mismatch or task not changed | Check notify string |
| nginx fails reload | Syntax error | `nginx -t` on host |
| default site still active | File task order | Re-run playbook |
| URI check fails | flush_handlers missing | Handlers run after all tasks |

## Cleanup

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.file   -a "path=/etc/nginx/sites-enabled/lab.conf state=absent"
```

---
*Source: Lesson 5 AP-05 · Next: [lab07](lab07-dynamic-inventory.md) · Deep dive: [handlers](../docs/playbooks/handlers-notify.md)*
