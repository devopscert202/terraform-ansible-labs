# Lab 04: Executing Loops in a Playbook

> **Goal:** Use `loop`, `loop_control`, and list variables to install packages and create users across webservers.
> **Time:** ~45 min · **Files:** `labs/playbooks/loops-packages.yml` · **Source:** Lesson 5 AP-03

## Before you start

- [lab03](lab03-nodejs-playbook.md) complete
- `web1` and `web2` reachable

## Concepts

Loops repeat a task for each item in a list. Prefer `loop` (modern) over legacy `with_items`.

```yaml
loop: "{{ my_list }}"
loop_control:
  label: "{{ item.name }}"
```

---

## Steps

### Step 1 — Review the playbook

```bash
cd ~/terraform-ansible-labs/ansible/extended/labs
cat playbooks/loops-packages.yml
```

Identify:

- `baseline_packages` list
- `lab_users` list of dictionaries
- `loop_control.label` on each loop

**Validate**

```bash
ansible-playbook --syntax-check playbooks/loops-packages.yml
```

---

### Step 2 — List what will be installed

```bash
grep -A6 baseline_packages playbooks/loops-packages.yml
```

**Validate**

Four packages: `htop`, `vim`, `curl`, `jq`.

---

### Step 3 — Run the playbook

```bash
ansible-playbook -i inventory/hosts.ini playbooks/loops-packages.yml
```

**Validate**

```text
PLAY RECAP *********************************************************************
web1   : ok=...  failed=0
web2   : ok=...  failed=0
```

Task output shows labels like `htop`, `deploy` instead of full JSON.

---

### Step 4 — Verify packages on web1

```bash
ansible -i inventory/hosts.ini web1 -b -m ansible.builtin.command -a "dpkg -l htop jq | tail -2"
```

**Validate**

Both packages show status `ii` (installed).

---

### Step 5 — Verify users exist

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.command -a "getent passwd deploy monitor"
```

**Validate**

Two lines with `/bin/bash` shells.

---

### Step 6 — Check deploy group membership

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.command -a "groups deploy"
```

**Validate**

Output includes `sudo`.

---

### Step 7 — Idempotency

```bash
ansible-playbook -i inventory/hosts.ini playbooks/loops-packages.yml
```

**Validate**

Package and user tasks report `ok`, not `changed`.

---

### Step 8 — Extend the loop (exercise)

Add `tree` to `baseline_packages` in the playbook, then re-run.

**Validate**

Only the new package task shows `changed`.

---

### Step 9 — Loop with `--limit`

```bash
ansible-playbook -i inventory/hosts.ini playbooks/loops-packages.yml --limit web1
```

**Validate**

Only `web1` in recap.

---

### Step 10 — Debug loop item count

Add a temporary debug task or run:

```bash
ansible -i inventory/hosts.ini web1 -m ansible.builtin.debug   -a "msg=4 packages defined in playbook"
```

**Validate**

Confirms you understand list length drives iteration count.

---

## Done when

- [ ] Playbook runs with `failed=0`
- [ ] All four packages installed
- [ ] Users `deploy` and `monitor` exist
- [ ] Second run is idempotent
- [ ] You added one package and saw a single change

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `item` undefined | Wrong loop variable | Use `{{ item }}` for simple lists, `{{ item.name }}` for dicts |
| authorized_key skipped | No local pubkey | Expected when `~/.ssh/id_ed25519.pub` missing |
| apt lock | Concurrent apt | Wait and retry |

## Cleanup

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.user   -a "name=deploy state=absent remove=yes"
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.user   -a "name=monitor state=absent remove=yes"
```

---
*Source: Lesson 5 AP-03 · Next: [lab05](lab05-conditionals.md) · Deep dive: [loops](../docs/playbooks/loops-and-conditionals.md)*
