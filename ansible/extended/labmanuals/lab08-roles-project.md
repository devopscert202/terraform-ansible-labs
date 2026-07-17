# Lab 08: Initializing Ansible Roles and Inventory (Lesson-End Project)

> **Goal:** Structure a multi-tier deployment using **roles** (`common`, `webserver`, `nodejs_app`), role dependencies, defaults, handlers, and a site playbook.
> **Time:** ~90 min · **Files:** `labs/roles/`, `labs/playbooks/site.yml` · **Source:** Lesson 6 LEP

## Before you start

- [lab07](lab07-dynamic-inventory.md) complete (or static inventory configured)
- Inventory lists `webservers` (web1, web2) and `appservers` (app1)
- Ubuntu 22.04 on all targets

## Project overview

You will deploy:

| Tier | Hosts | Roles applied |
|------|-------|---------------|
| Web | webservers | `common` → `webserver` |
| App | appservers | `common` → `nodejs_app` |

Role layout follows Ansible Galaxy conventions:

```
roles/
  common/
    tasks/main.yml
    defaults/main.yml
    meta/main.yml
  webserver/
    tasks/main.yml
    handlers/main.yml
    templates/index.html.j2
    defaults/main.yml
    meta/main.yml      # depends on common
  nodejs_app/
    tasks/main.yml
    handlers/main.yml
    templates/
    defaults/main.yml
    meta/main.yml      # depends on common
```

---

## Part A — Understand role anatomy

### Step A1 — List role directories

```bash
cd ~/terraform-ansible-labs/ansible/extended/labs
find roles -type f | sort
```

**Validate**

At least 15 files across three roles (tasks, defaults, handlers, templates, meta).

---

### Step A2 — Read `common` role

```bash
cat roles/common/defaults/main.yml
cat roles/common/tasks/main.yml
```

**Validate**

- Defaults define `common_packages` list
- Tasks install packages and create `/etc/ansible-lab-common`

---

### Step A3 — Read role dependencies

```bash
cat roles/webserver/meta/main.yml
cat roles/nodejs_app/meta/main.yml
```

**Validate**

Both declare `dependencies: - role: common`.

---

### Step A4 — Variable precedence exercise

```bash
cat group_vars/all.yml
cat roles/webserver/defaults/main.yml
```

**Validate**

`group_vars/all.yml` can override role defaults when keys match (e.g. `nodejs_app_port`).

---

## Part B — Validate roles independently

### Step B1 — Syntax check site playbook

```bash
ansible-playbook --syntax-check playbooks/site.yml
```

**Validate**

```text
playbook: playbooks/site.yml
```

---

### Step B2 — Check role paths

```bash
ansible-playbook -i inventory/hosts.ini playbooks/site.yml --list-tasks | head -30
```

**Validate**

Tasks from `common` and `webserver` appear for webservers; `common` and `nodejs_app` for appservers.

---

### Step B3 — Dry run

```bash
ansible-playbook -i inventory/hosts.ini playbooks/site.yml --check
```

**Validate**

No fatal errors; note apt check-mode warnings.

---

### Step B4 — Deploy full stack

```bash
ansible-playbook -i inventory/hosts.ini playbooks/site.yml
```

**Validate**

```text
PLAY RECAP *********************************************************************
web1   : failed=0
web2   : failed=0
app1   : failed=0
```

---

## Part C — Verify web tier

### Step C1 — Common marker file

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.command   -a "cat /etc/ansible-lab-common"
```

**Validate**

```text
configured_by=ansible-extended
role=common
```

---

### Step C2 — nginx serving role template

```bash
ansible -i inventory/hosts.ini web1 -m ansible.builtin.uri   -a "url=http://127.0.0.1/ return_content=yes"
```

**Validate**

HTML contains `Configured by Ansible role: webserver` and hostname.

---

### Step C3 — Package verification

```bash
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.command   -a "dpkg -l nginx | tail -1"
```

**Validate**

nginx installed (`ii`).

---

## Part D — Verify app tier

### Step D1 — Node.js version

```bash
ansible -i inventory/hosts.ini appservers -b -m ansible.builtin.command -a "node --version"
```

**Validate**

`v20.x.x`

---

### Step D2 — Application service

```bash
ansible -i inventory/hosts.ini appservers -b -m ansible.builtin.command   -a "systemctl is-active lab-app"
```

**Validate**

`active`

---

### Step D3 — HTTP response

```bash
ansible -i inventory/hosts.ini app1 -m ansible.builtin.uri   -a "url=http://127.0.0.1:3000/ return_content=yes" -b
```

**Validate**

Hello message includes hostname.

---

## Part E — Role customization

### Step E1 — Override web port in play (extra vars)

```bash
ansible-playbook -i inventory/hosts.ini playbooks/site.yml -e "webserver_port=8080" --limit web1
```

**Validate**

Template still deploys (port variable used in HTML); note nginx listen config uses defaults unless you extend template.

---

### Step E2 — Add package to common defaults

Edit `roles/common/defaults/main.yml` — add `git` to `common_packages`.

```bash
ansible-playbook -i inventory/hosts.ini playbooks/site.yml --tags never 2>/dev/null || ansible-playbook -i inventory/hosts.ini playbooks/site.yml
```

**Validate**

```bash
ansible -i inventory/hosts.ini all -b -m ansible.builtin.command -a "which git"
```

`git` found on all hosts.

---

### Step E3 — Handler test on web tier

Modify `roles/webserver/templates/index.html.j2` (add footer line), re-run site playbook for webservers.

**Validate**

`RUNNING HANDLER [Reload webserver]` in output.

---

### Step E4 — Idempotency

```bash
ansible-playbook -i inventory/hosts.ini playbooks/site.yml
```

**Validate**

Predominantly `ok`, minimal `changed`.

---

## Part F — Project deliverables checklist

Document for your portfolio:

1. Inventory diagram (static or dynamic)
2. Role dependency graph
3. Variables at each layer (defaults vs group_vars)
4. Evidence: `PLAY RECAP` with zero failures

### Step F1 — Role dependency diagram (text)

```
site.yml
 ├── webservers: common → webserver
 └── appservers: common → nodejs_app
```

**Validate**

You can draw this from memory.

---

### Step F2 — ansible-lint (optional)

```bash
pip install ansible-lint 2>/dev/null; ansible-lint playbooks/site.yml || true
```

**Validate**

No critical failures (warnings acceptable in lab).

---

## Design decisions

| Choice | Why |
|--------|-----|
| Role per concern | Reuse `common` on all tiers |
| `meta/main.yml` dependencies | DRY baseline packages |
| Defaults in `defaults/main.yml` | Easy override without editing tasks |
| FQCN modules | Future-proof for Ansible 2.14+ |
| NodeSource 20 | Supported on Ubuntu 22.04 |

---

## Done when

- [ ] All three roles present with standard layout
- [ ] `site.yml` applies correct roles per group
- [ ] Web tier serves nginx with role template
- [ ] App tier runs Node 20 via systemd
- [ ] `/etc/ansible-lab-common` on all hosts
- [ ] Second playbook run is idempotent
- [ ] You customized one default and observed change

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Role not found | Wrong `roles_path` | Run from `labs/` or set `roles_path` in ansible.cfg |
| Dependency loop | Circular meta | Ensure only leaf roles depend on common |
| Handler not running | Template not changed | Verify task reports `changed` |
| Node install fails | GPG/keyring | Compare with lab03 nodejs playbook |
| nginx default page | Template path wrong | Check `roles/webserver/templates/` |

## Cleanup

```bash
ansible-playbook -i inventory/hosts.ini playbooks/site.yml --extra-vars "cleanup=true" 2>/dev/null || true
ansible -i inventory/hosts.ini webservers -b -m ansible.builtin.apt -a "name=nginx state=absent autoremove=yes"
ansible -i inventory/hosts.ini appservers -b -m ansible.builtin.systemd -a "name=lab-app state=stopped enabled=no"
```

---
*Source: Lesson 6 LEP · Next: [lab09](lab09-break-fix-drills.md) · Deep dive: [playbook structure](../docs/playbooks/playbook-structure.md)*
