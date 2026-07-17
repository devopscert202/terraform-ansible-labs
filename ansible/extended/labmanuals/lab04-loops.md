# Lab 04: Executing Loops in a Playbook

> **Goal:** Use `loop`, `loop_control`, and list variables to install packages and create users across webservers.
> **Time:** ~45 min · **Files:** `labs/playbooks/loops-packages.yml` · **Source:** Lesson 5 AP-03
> **Interactive:** [loops-conditionals.html](../html/loops-conditionals.html)

## Before you start

- [lab03](lab03-nodejs-playbook.md) complete
- `web1` and `web2` reachable via SSH
- Read [loops-and-conditionals.md](../docs/playbooks/loops-and-conditionals.md) — Loop section

## Concepts

Loops repeat a task for each item in a list. Prefer `loop` (modern) over legacy `with_items`.

```yaml
loop: "{{ my_list }}"
loop_control:
  label: "{{ item.name }}"
```

| Pattern | `item` value |
|---------|-------------|
| Simple list | string (package name) |
| List of dicts | dict with keys `.name`, `.groups` |

---

## Part A — Understand the playbook

### Step 1 — Enter lab directory

```bash
cd ~/terraform-ansible-labs/ansible/extended/labs
pwd
```

**Validate**

Path ends with `ansible/extended/labs`.

---

### Step 2 — Review loops-packages.yml

```bash
cat playbooks/loops-packages.yml
```

Identify three task groups:
1. Package loop over `baseline_packages`
2. User loop over `lab_users` (dict items)
3. Conditional SSH key task with `when`

**Validate**

You can point to `loop:` and `loop_control:` lines in the file.

---

### Step 3 — Syntax check

```bash
ansible-playbook --syntax-check playbooks/loops-packages.yml
```

**Validate**

```text
playbook: playbooks/loops-packages.yml
```

No `ERROR!` lines.

---

### Step 4 — List packages to be installed

```bash
grep -A6 "baseline_packages:" playbooks/loops-packages.yml
```

**Validate**

Four packages: `htop`, `vim`, `curl`, `jq`.

---

### Step 5 — List users to be created

```bash
grep -A10 "lab_users:" playbooks/loops-packages.yml
```

**Validate**

Users `deploy` (groups: sudo) and `monitor` (groups: adm).

---

## Part B — Execute the playbook

### Step 6 — First run

```bash
ansible-playbook -i inventory/hosts.ini playbooks/loops-packages.yml
```

**Validate**

```text
PLAY RECAP *********************************************************************
web1   : ok=...  changed=...  unreachable=0  failed=0
web2   : ok=...  changed=...  unreachable=0  failed=0
```

Task output shows labels `htop`, `vim`, `deploy` — not full JSON blobs.

---

### Step 7 — Verify packages on web1

```bash
ansible -i inventory/hosts.ini web1 -b -m ansible.builtin.command   -a "dpkg -l htop jq | tail -2"
```

**Validate**

Both packages show status `ii` (installed).

```bash
ansible -i inventory/hosts.ini web1 -b -m ansible.builtin.command   -a "which htop vim curl jq"
```

All four binaries found.

---

### Step 8 — Verify users exist

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.command   -a "getent passwd deploy monitor"
```

**Validate**

Two lines with `/bin/bash` shells and distinct UIDs.

---

### Step 9 — Check deploy group membership

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.command   -a "groups deploy"
```

**Validate**

Output includes `sudo` on both webservers.

---

### Step 10 — Verify monitor group membership

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.command   -a "groups monitor"
```

**Validate**

Output includes `adm`.

---

## Part C — Idempotency and limits

### Step 11 — Second run (idempotency)

```bash
ansible-playbook -i inventory/hosts.ini playbooks/loops-packages.yml
```

**Validate**

Package and user tasks report `ok`, not `changed`. `PLAY RECAP` shows `changed=0` or minimal changes.

---

### Step 12 — Run with --limit web1

```bash
ansible-playbook -i inventory/hosts.ini playbooks/loops-packages.yml --limit web1
```

**Validate**

Only `web1` appears in recap. `web2` not targeted.

---

### Step 13 — Verbose loop output

```bash
ansible-playbook -i inventory/hosts.ini playbooks/loops-packages.yml -v 2>&1 | grep -i "loop"
```

**Validate**

You see loop iteration references in verbose output.

---

## Part D — Extend the playbook

### Step 14 — Add package to list

Edit `playbooks/loops-packages.yml` — add `tree` to `baseline_packages`:

```yaml
baseline_packages:
  - htop
  - vim
  - curl
  - jq
  - tree
```

**Validate**

```bash
grep tree playbooks/loops-packages.yml
```

Shows `tree` in list.

---

### Step 15 — Re-run and observe single change

```bash
ansible-playbook -i inventory/hosts.ini playbooks/loops-packages.yml
```

**Validate**

Only `tree` package task shows `changed` on each host. Other tasks `ok`.

```bash
ansible -i inventory/hosts.ini web1 -b -m ansible.builtin.command -a "tree --version"
```

`tree` command succeeds.

---

### Step 16 — Revert tree addition (optional)

Remove `tree` from list to keep lab state clean, or leave for later labs.

---

## Part E — SSH key conditional

### Step 17 — Observe authorized_key behavior

```bash
test -f ~/.ssh/id_ed25519.pub && echo "Key exists" || echo "Key missing (task will skip)"
```

**Validate**

If key missing, playbook skips authorized_key task — expected behavior per `when` clause.

---

### Step 18 — Debug package count message

The playbook includes a debug task reporting package count. Confirm in last run output:

```text
"msg": "Installed 4 packages on web1"
```

(Or 5 if you added tree.)

---

## Done when

- [ ] Syntax check passes
- [ ] Playbook runs with `failed=0` on both webservers
- [ ] All baseline packages installed
- [ ] Users `deploy` and `monitor` exist with correct groups
- [ ] Second run is idempotent
- [ ] You added one package and saw targeted `changed`
- [ ] You used `--limit` successfully

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `item` undefined | Wrong loop variable | `{{ item }}` for lists, `{{ item.name }}` for dicts |
| authorized_key skipped | No local pubkey | Expected — or create `~/.ssh/id_ed25519.pub` |
| apt lock | Concurrent apt | Wait; don't run apt from SSH session simultaneously |
| `failed=1` on one host | Partial state | Fix host; re-run playbook (idempotent) |

## Cleanup

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.user   -a "name=deploy state=absent remove=yes"
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.user   -a "name=monitor state=absent remove=yes"
```

---
*Source: Lesson 5 AP-03 · Next: [lab05](lab05-conditionals.md) · Deep dive: [loops](../docs/playbooks/loops-and-conditionals.md)*
