# Lab 09: Break-Fix Drills

> **Goal:** Diagnose and repair common Ansible failures — YAML syntax, privilege escalation, handler names, FQCN modules, and inventory variables.
> **Time:** ~60–90 min · **Files:** `labs/break-fix/` · **Source:** Synthesis lab (track finale)
> **Interactive:** [break-fix.html](../html/break-fix.html)

## Before you start

- [lab08](lab08-roles-project.md) complete
- Comfortable reading Ansible error messages and stack traces
- Do **not** open `solutions/` until you have attempted each fix
- Working directory: `~/terraform-ansible-labs/ansible/extended/labs`

## How this lab works

Each drill ships a **broken** artifact. Your workflow for every drill:

1. **Reproduce** — run the broken file and capture full error output
2. **Read** — identify the first fatal error line and file reference
3. **Isolate** — determine category (YAML, become, handler, FQCN, inventory)
4. **Fix** — edit the broken file OR apply fix in place
5. **Verify** — re-run until `failed=0` or `pong` success
6. **Document** — record error fragment and root cause in your notes

This mirrors production incident response for configuration management pipelines.

## Troubleshooting workflow reference

```
Reproduce → Read error → Isolate scope → Apply fix → Verify → Document
```

| Error category | First command |
|----------------|---------------|
| YAML | `ansible-playbook --syntax-check file.yml` |
| Permission | Check for `become: true` or `-b` |
| Handler | Compare `notify` vs handler `name` |
| FQCN | Use `ansible.builtin.*` modules |
| Connection | `ansible host -m ansible.builtin.ping -vvv` |
| Interpreter | Check `ansible_python_interpreter` in inventory |

---

# Drill 01 — YAML indentation

## Background

YAML is whitespace-sensitive. Ansible playbooks are lists of dictionaries — misaligned keys cause parse failures before any host is contacted.

## Step 1.1 — Run broken playbook

```bash
cd ~/terraform-ansible-labs/ansible/extended/labs
ansible-playbook -i inventory/hosts.ini break-fix/drill-01-broken-yaml.yml
```

**Validate (expected failure)**

```text
ERROR! We were unable to read valid YAML
```

Or parser error referencing line with bad indent.

**Capture**

Copy the full error message to your notes. Note the line number if provided.

---

## Step 1.2 — Syntax check isolation

```bash
ansible-playbook --syntax-check break-fix/drill-01-broken-yaml.yml
```

**Validate**

Same YAML error — confirms parse-time failure (not host-related).

---

## Step 1.3 — Inspect broken file

```bash
cat -n break-fix/drill-01-broken-yaml.yml
```

**Validate**

Line with `ansible.builtin.apt` has **one fewer space** than `name:` under the task.

```yaml
    - name: Install curl
     ansible.builtin.apt:    # ← 5 spaces — WRONG (need 6)
```

---

## Step 1.4 — Predict the fix

Before editing, write in notes: "Module key must align with `name:` under the `-` task item."

---

## Step 1.5 — Apply fix

Option A: Edit `drill-01-broken-yaml.yml` directly — add one space before `ansible.builtin.apt`.

Option B: Compare with solution:

```bash
diff break-fix/drill-01-broken-yaml.yml break-fix/solutions/drill-01-fixed.yml
```

**Validate**

Diff shows only indentation change on module line.

---

## Step 1.6 — Verify fixed playbook

```bash
ansible-playbook -i inventory/hosts.ini break-fix/solutions/drill-01-fixed.yml
```

**Validate**

```text
PLAY RECAP *********************************************************************
web1   : failed=0
web2   : failed=0
```

---

## Step 1.7 — Drill 01 documentation

| Field | Your notes |
|-------|-----------|
| Error fragment | |
| Root cause | YAML indentation |
| Fix applied | Aligned apt module with task name |

---

# Drill 02 — Missing become

## Background

Package installation requires root privileges. Without `become: true`, apt runs as `ubuntu` user and fails with permission errors.

## Step 2.1 — Run broken playbook

```bash
ansible-playbook -i inventory/hosts.ini break-fix/drill-02-missing-become.yml
```

**Validate (expected failure)**

```text
E: Could not open lock file /var/lib/dpkg/lock
```

Or `Permission denied` / `FAILED!` on apt task.

---

## Step 2.2 — Identify missing privilege escalation

```bash
grep -n become break-fix/drill-02-missing-become.yml || echo "become not found (ROOT CAUSE)"
```

**Validate**

No `become: true` at play level.

---

## Step 2.3 — Compare with solution

```bash
diff break-fix/drill-02-missing-become.yml break-fix/solutions/drill-02-fixed.yml
```

**Validate**

Solution adds `become: true` under play definition.

---

## Step 2.4 — Verify solution

```bash
ansible-playbook -i inventory/hosts.ini break-fix/solutions/drill-02-fixed.yml
```

**Validate**

`failed=0` on all targeted hosts.

---

## Step 2.5 — Ad hoc equivalent

Demonstrate same fix with flag:

```bash
ansible -i inventory/hosts.ini web1 -b -m ansible.builtin.apt -a "name=curl state=present"
```

**Validate**

Succeeds with `-b` (become).

---

## Step 2.6 — Drill 02 documentation

| Field | Your notes |
|-------|-----------|
| Error fragment | dpkg lock / permission denied |
| Root cause | Missing become for apt |
| Fix | become: true at play level |

---

# Drill 03 — Handler name mismatch

## Background

The most insidious Ansible bug: play **succeeds** but handler never runs because `notify` string does not exactly match handler `name`.

## Step 3.1 — Run broken playbook (first time)

```bash
ansible-playbook -i inventory/hosts.ini break-fix/drill-03-handler-mismatch.yml
```

**Validate**

Play may complete with `failed=0` — **misleading success**.

---

## Step 3.2 — Check for RUNNING HANDLER

```bash
ansible-playbook -i inventory/hosts.ini break-fix/drill-03-handler-mismatch.yml 2>&1 | grep -i "RUNNING HANDLER" || echo "NO HANDLER EXECUTED"
```

**Validate**

`NO HANDLER EXECUTED` — even when config task shows `changed`.

---

## Step 3.3 — Compare notify vs handler names

```bash
grep notify break-fix/drill-03-handler-mismatch.yml
grep -A2 "handlers:" break-fix/drill-03-handler-mismatch.yml
```

**Validate**

Mismatch example: `notify: restart nginx` vs `name: Restart nginx` (case/word difference).

---

## Step 3.4 — Predict behavior

Write in notes: "Ansible queues handlers by exact string match. Case and spacing matter."

---

## Step 3.5 — Run fixed solution

```bash
ansible-playbook -i inventory/hosts.ini break-fix/solutions/drill-03-fixed.yml
```

**Validate**

```text
RUNNING HANDLER [Restart nginx]
```

Appears when config changes.

---

## Step 3.6 — Second run idempotency

```bash
ansible-playbook -i inventory/hosts.ini break-fix/solutions/drill-03-fixed.yml 2>&1 | grep "RUNNING HANDLER" || echo "No handler on idempotent run (correct)"
```

**Validate**

No handler when nothing changed.

---

## Step 3.7 — Drill 03 documentation

| Field | Your notes |
|-------|-----------|
| Error fragment | (none — silent failure) |
| Root cause | notify ≠ handler name |
| Detection | Missing RUNNING HANDLER in output |

---

# Drill 04 — Non-FQCN module

## Background

Ansible 2.10+ requires fully qualified collection names (FQCN). Short names may work with warnings or fail in strict environments.

## Step 4.1 — Run broken playbook

```bash
ansible-playbook -i inventory/hosts.ini break-fix/drill-04-non-fqcn.yml
```

**Validate**

May succeed with warning:

```text
[DEPRECATION WARNING]: ...
```

Or fail with module not found in strict ansible.cfg.

---

## Step 4.2 — Identify short module name

```bash
grep -E "^\s+- (ping|apt|service):" break-fix/drill-04-non-fqcn.yml
```

**Validate**

Uses `ping` instead of `ansible.builtin.ping`.

---

## Step 4.3 — Run fixed solution

```bash
ansible-playbook -i inventory/hosts.ini break-fix/solutions/drill-04-fixed.yml
```

**Validate**

`ansible.builtin.ping` succeeds without deprecation warning.

---

## Step 4.4 — ansible-doc FQCN reference

```bash
ansible-doc ansible.builtin.ping | head -15
```

**Validate**

Documentation found for FQCN module.

---

## Step 4.5 — Drill 04 documentation

| Field | Your notes |
|-------|-----------|
| Warning/error | DEPRECATION or not found |
| Root cause | Short module name |
| Fix | ansible.builtin.ping |

---

# Drill 05 — Wrong Python interpreter

## Background

Ubuntu 22.04 does not provide `/usr/bin/python` (Python 2). Inventory must set `ansible_python_interpreter=/usr/bin/python3`.

## Step 5.1 — Run ping with broken inventory

```bash
ansible -i break-fix/drill-05-broken-inventory.ini webservers -m ansible.builtin.ping
```

**Validate (expected failure)**

```text
/usr/bin/python: not found
```

Or `/usr/bin/python: No such file or directory`

---

## Step 5.2 — Inspect broken inventory

```bash
cat break-fix/drill-05-broken-inventory.ini
```

**Validate**

`ansible_python_interpreter=/usr/bin/python` (Python 2 path).

---

## Step 5.3 — Test fixed inventory

```bash
ansible -i break-fix/solutions/drill-05-fixed-inventory.ini webservers -m ansible.builtin.ping
```

**Validate**

```text
"pong"
```

On all webservers.

---

## Step 5.4 — Compare inventories

```bash
diff break-fix/drill-05-broken-inventory.ini break-fix/solutions/drill-05-fixed-inventory.ini
```

**Validate**

Only interpreter line differs (python → python3).

---

## Step 5.5 — Verify extended lab inventory

```bash
grep python inventory/hosts.ini
```

**Validate**

Extended lab `hosts.ini` already uses `python3` — explains why other labs work.

---

## Step 5.6 — Drill 05 documentation

| Field | Your notes |
|-------|-----------|
| Error fragment | python: not found |
| Root cause | Python 2 interpreter on Ubuntu 22.04 |
| Fix | ansible_python_interpreter=/usr/bin/python3 |

---

# Drill 06 — Speed run (optional challenge)

## Step 6.1 — Fix all drills without solutions

Reset any edited files. Fix all five broken artifacts in under 30 minutes.

**Validate**

```bash
for f in break-fix/solutions/drill-0{1,2,3,4}-fixed.yml; do
  ansible-playbook -i inventory/hosts.ini "$f" --syntax-check
done
ansible -i break-fix/solutions/drill-05-fixed-inventory.ini webservers -m ansible.builtin.ping
```

All syntax checks pass. Ping returns pong.

---

# Drill 07 — Diagnostic toolkit practice

## Step 7.1 — Syntax check all broken files

```bash
for f in break-fix/drill-*.yml; do
  echo "=== $f ==="
  ansible-playbook --syntax-check "$f" 2>&1 | tail -3
done
```

**Validate**

Drill 01 fails syntax check. Others may pass syntax but fail at runtime.

---

## Step 7.2 — Verbose ping baseline

```bash
ansible -i inventory/hosts.ini web1 -m ansible.builtin.ping -vvv 2>&1 | grep -E "python|SSH|SUCCESS" | head -10
```

**Validate**

Shows Python 3 interpreter path used for module execution.

---

# Comprehensive error reference

| Drill | File | Typical error | Root cause | Fix |
|-------|------|---------------|------------|-----|
| 01 | drill-01-broken-yaml.yml | could not read valid YAML | Bad indent | Align module with name |
| 02 | drill-02-missing-become.yml | dpkg lock permission | No become | become: true |
| 03 | drill-03-handler-mismatch.yml | (silent) | notify ≠ handler | Exact name match |
| 04 | drill-04-non-fqcn.yml | DEPRECATION WARNING | Short module | ansible.builtin.* |
| 05 | drill-05-broken-inventory.ini | python not found | python2 path | python3 interpreter |

---

# Production scenarios (discussion)

## Scenario A: CI pipeline fails after AMI upgrade

**Symptoms:** All plays fail with python not found.

**Diagnosis:** New AMI removed python2 symlink.

**Fix:** Update `group_vars/all.yml` with `ansible_python_interpreter: /usr/bin/python3`.

---

## Scenario B: Config deployed but service stale

**Symptoms:** Playbook ok, old behavior persists.

**Diagnosis:** Handler name mismatch — check RUNNING HANDLER.

**Fix:** Align notify and handler names; verify task reports `changed`.

---

## Scenario C: Intermittent apt failures

**Symptoms:** Permission denied on some hosts only.

**Diagnosis:** Missing become on subset of plays.

**Fix:** Standardize `become: true` in role defaults or play headers.

---

# Done when

- [ ] Fixed YAML indentation drill (Drill 01)
- [ ] Fixed missing become drill (Drill 02)
- [ ] Fixed handler mismatch drill (Drill 03)
- [ ] Converted short module to FQCN (Drill 04)
- [ ] Fixed Python interpreter in inventory (Drill 05)
- [ ] Documented one full error message and fix per drill
- [ ] Completed speed run OR documented time for each drill
- [ ] Can explain troubleshooting workflow without notes

## Final knowledge check

1. What is the first command for a YAML suspicion?
2. How do you detect handler mismatch if play succeeds?
3. Why is Drill 03 considered a "silent" failure?
4. What changed in Ubuntu 22.04 affecting Drill 05?
5. When would you use `-vvv` on ping?

## Track completion

Congratulations — you have completed the Ansible Extended track (Labs 01–09).

| Lab | Topic |
|-----|-------|
| 01 | Ad hoc modules |
| 02 | Facts |
| 03 | Playbooks / Node.js |
| 04 | Loops |
| 05 | Conditionals |
| 06 | Handlers |
| 07 | Dynamic inventory |
| 08 | Roles project |
| 09 | Break-fix |

## Step 7.3 — Create personal runbook entry

Create a runbook snippet in your notes with this template (fill in from your session):

```markdown
## Ansible break-fix runbook

### YAML errors
- Command: ansible-playbook --syntax-check <file>
- Common fix: fix indentation (2 spaces, align module with name)

### Permission errors
- Symptom: dpkg lock, permission denied
- Fix: become: true or ansible -b

### Handler not running
- Symptom: play ok, service stale
- Check: grep RUNNING HANDLER; compare notify vs handler name

### FQCN warnings
- Fix: ansible.builtin.<module>

### Python interpreter
- Symptom: /usr/bin/python not found
- Fix: ansible_python_interpreter=/usr/bin/python3
```

**Validate**

Runbook section completed with at least one real error you encountered.

---

## Step 7.4 — Peer review exercise

Exchange error messages with a classmate. Diagnose each other's captured error without seeing the drill file.

**Validate**

Correctly identified error category (YAML/become/handler/FQCN/interpreter) for two peer errors.

---

## Step 7.5 — ansible-lint on solutions (optional)

```bash
pip install ansible-lint 2>/dev/null || true
ansible-lint break-fix/solutions/drill-01-fixed.yml 2>&1 || true
```

**Validate**

No critical failures on solution playbooks (style warnings acceptable).

---

## Step 7.6 — Map drills to interactive HTML

Open `../html/break-fix.html` and match each drill card to your lab experience.

**Validate**

You can navigate the troubleshooting workflow diagram and failure mode cards.

---

## Extended reference: verbosity levels

| Level | Flag | Use |
|-------|------|-----|
| 0 | (default) | Normal output |
| 1 | `-v` | Task results |
| 2 | `-vv` | Task inputs |
| 3 | `-vvv` | Connection debugging |
| 4 | `-vvvv` | SSH connection tracing |

Example:

```bash
ansible -i inventory/hosts.ini web1 -m ansible.builtin.ping -vvv
```

---

## Extended reference: common ansible-playbook exit codes

| Exit code | Meaning |
|-----------|---------|
| 0 | Success |
| 1 | Generic failure |
| 2 | One or more hosts failed |
| 4 | Host unreachable |
| 99 | User interrupted |

---

## Instructor sign-off checklist

| Criterion | Student | Instructor |
|-----------|---------|------------|
| Drill 01 fixed | ☐ | ☐ |
| Drill 02 fixed | ☐ | ☐ |
| Drill 03 fixed | ☐ | ☐ |
| Drill 04 fixed | ☐ | ☐ |
| Drill 05 fixed | ☐ | ☐ |
| Error log submitted | ☐ | ☐ |
| Runbook entry created | ☐ | ☐ |

---

```bash
# Optional cleanup
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.apt   -a "name=curl state=absent" 2>/dev/null || true
```

---
*Source: Synthesis · Track complete · [README](README.md) · [break-fix.html](../html/break-fix.html) · Return to [catalog](../html/index.html)*
