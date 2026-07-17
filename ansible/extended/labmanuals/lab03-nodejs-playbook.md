# Lab 03: Installing Node.js with a Playbook

> **Goal:** Write and run a playbook that installs **Node.js 20 LTS** on Ubuntu 22.04 and deploys a systemd-managed application.
> **Time:** ~60 min · **Files:** `labs/playbooks/nodejs.yml`, `labs/playbooks/templates/` · **Source:** Lesson 5 LEP / AP-01

## Before you start

- [lab02](lab02-facts.md) complete
- `app1` in inventory points to an Ubuntu 22.04 appserver (can be same as a web node for small labs)
- No deprecated `apt_key` or Node 0.10 — we use NodeSource with `signed-by` keyring

## Architecture

```
control node  --ansible-playbook-->  app1 (Ubuntu 22.04)
                                      ├── Node.js 20
                                      ├── /opt/lab-app/app.js
                                      └── systemd: lab-app.service
```

---

## Steps

### Step 1 — Review the playbook

```bash
cd ~/terraform-ansible-labs/ansible/extended/labs
less playbooks/nodejs.yml
```

Note:

- FQCN modules throughout
- NodeSource repo with `/etc/apt/keyrings/nodesource.gpg`
- Templates for app and systemd unit
- Handlers restart the app when files change

**Validate**

```bash
ansible-playbook --syntax-check playbooks/nodejs.yml
```

```text
playbook: playbooks/nodejs.yml
```

No syntax errors.

---

### Step 2 — Review group variables

```bash
cat group_vars/all.yml
```

**Validate**

```yaml
nodejs_version: "20"
nodejs_app_port: 3000
nodejs_app_name: lab-app
```

---

### Step 3 — Check mode (optional)

```bash
ansible-playbook -i inventory/hosts.ini playbooks/nodejs.yml --check
```

**Validate**

Play completes or shows expected `changed` simulation. Warnings about apt in check mode are acceptable.

---

### Step 4 — Run the playbook

```bash
ansible-playbook -i inventory/hosts.ini playbooks/nodejs.yml
```

**Validate**

```text
PLAY RECAP *********************************************************************
app1   : ok=...  changed=...  unreachable=0  failed=0
```

`failed=0` on all hosts.

---

### Step 5 — Verify Node.js version on target

```bash
ansible -i inventory/hosts.ini appservers -m ansible.builtin.command -a "node --version" -b
```

**Validate**

```text
v20.x.x
```

Major version is **20**, not 0.10 or 18 unless you changed defaults.

---

### Step 6 — Verify systemd service

```bash
ansible -i inventory/hosts.ini appservers -b -m ansible.builtin.command \
  -a "systemctl is-active lab-app"
```

**Validate**

```text
active
```

---

### Step 7 — Test HTTP response locally on app server

```bash
ansible -i inventory/hosts.ini app1 -m ansible.builtin.uri \
  -a "url=http://127.0.0.1:3000/ return_content=yes" -b
```

**Validate**

```text
"content": "Hello from lab-app on port 3000\n"
```

---

### Step 8 — Idempotency second run

```bash
ansible-playbook -i inventory/hosts.ini playbooks/nodejs.yml
```

**Validate**

Most tasks show `ok` (not `changed`). Handlers should not fire unless templates changed.

---

### Step 9 — Trigger handler by changing port

```bash
ansible-playbook -i inventory/hosts.ini playbooks/nodejs.yml -e "nodejs_app_port=3001"
```

**Validate**

```bash
ansible -i inventory/hosts.ini app1 -m ansible.builtin.uri \
  -a "url=http://127.0.0.1:3001/ return_content=yes" -b
```

Response succeeds on port **3001**.

---

### Step 10 — Inspect deployed files

```bash
ansible -i inventory/hosts.ini app1 -m ansible.builtin.command \
  -a "ls -la /opt/lab-app/" -b
```

**Validate**

`app.js` owned by `ubuntu`, mode `644`.

---

## Playbook design notes

| Decision | Rationale |
|----------|-----------|
| NodeSource 20.x | Supported LTS on Ubuntu 22.04 |
| `get_url` + `apt_repository` | Replaces deprecated `apt_key` |
| systemd unit | Production-style process management |
| Handlers | Restart only when app files change |

---

## Done when

- [ ] Syntax check passes
- [ ] Playbook completes with `failed=0`
- [ ] `node --version` shows v20.x
- [ ] `lab-app` service is active
- [ ] HTTP check returns hello message
- [ ] Second run is mostly idempotent

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| apt GPG error | Keyring path wrong | Verify `/etc/apt/keyrings/nodesource.gpg` exists |
| Service failed | Port in use | `ss -tlnp | grep 3000`; change `nodejs_app_port` |
| Template not found | Wrong path | Templates live in `playbooks/templates/` |
| app1 unreachable | Inventory IP | Update `inventory/hosts.ini` |



---

## Part F — Playbook deep dive

### Step 11 — Inspect NodeSource keyring task

```bash
grep -A15 "nodesource" playbooks/nodejs.yml
```

**Validate**

Uses `ansible.builtin.get_url` and `ansible.builtin.apt_repository` with `signed-by` — no deprecated `apt_key`.

---

### Step 12 — Verify keyring on target

```bash
ansible -i inventory/hosts.ini app1 -b -m ansible.builtin.command   -a "ls -la /etc/apt/keyrings/nodesource.gpg"
```

**Validate**

File exists with root ownership.

---

### Step 13 — Inspect deployed application

```bash
ansible -i inventory/hosts.ini app1 -b -m ansible.builtin.command   -a "cat /opt/lab-app/app.js"
```

**Validate**

JavaScript references `nodejs_app_port` and hostname from template.

---

### Step 14 — Inspect systemd unit

```bash
ansible -i inventory/hosts.ini app1 -b -m ansible.builtin.command   -a "systemctl cat lab-app"
```

**Validate**

Unit file shows `ExecStart` with node and app path.

---

### Step 15 — Check listening port

```bash
ansible -i inventory/hosts.ini app1 -b -m ansible.builtin.command   -a "ss -tlnp | grep 3000"
```

**Validate**

node process listening on 127.0.0.1:3000 (or configured port).

---

## Part G — Handler verification

### Step 16 — Confirm handler names match

```bash
grep -E "notify:|name:" playbooks/nodejs.yml | head -20
```

**Validate**

Every `notify:` string exactly matches a handler `name:`.

---

### Step 17 — Handler skip on idempotent run

```bash
ansible-playbook -i inventory/hosts.ini playbooks/nodejs.yml 2>&1 | grep -i "RUNNING HANDLER" || echo "No handlers (expected on idempotent run)"
```

**Validate**

No `RUNNING HANDLER` when templates unchanged.

---

## Knowledge check

1. Why is Node 20 installed from NodeSource instead of Ubuntu default?
2. What triggers the application restart handler?
3. Where are `nodejs_app_port` and `nodejs_version` defined?
4. What does `--syntax-check` validate vs `--check`?

## Additional troubleshooting

| Symptom | Diagnostic command | Fix |
|---------|-------------------|-----|
| GPG error | `ls /etc/apt/keyrings/` | Re-run playbook from keyring task |
| Port conflict | `ss -tlnp` | Change `nodejs_app_port` in group_vars |
| Handler not run | Compare notify/handler names | Exact string match |
| Template error | `ansible-playbook --syntax-check` | Fix Jinja2 syntax |

## Cleanup

```bash
ansible -i inventory/hosts.ini appservers -b -m ansible.builtin.systemd \
  -a "name=lab-app state=stopped enabled=no"
ansible -i inventory/hosts.ini appservers -b -m ansible.builtin.file \
  -a "path=/opt/lab-app state=absent"
ansible -i inventory/hosts.ini appservers -b -m ansible.builtin.file \
  -a "path=/etc/systemd/system/lab-app.service state=absent"
```

---
*Source: Lesson 5 LEP · Next: [lab04](lab04-loops.md) · Deep dive: [playbook structure](../docs/playbooks/playbook-structure.md)*
