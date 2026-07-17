# Lab 05: Variables and Templates

> **Goal:** Deploy a Jinja2-templated MOTD file using group variables from inventory and the `ansible.builtin.template` module.
> **Time:** ~60 min · **Difficulty:** Intermediate · **Files:** `labs/playbooks/vars-demo.yml`, `labs/templates/motd.j2`, `labs/inventory/group_vars/webservers.yml`

## Overview

Variables make playbooks reusable across environments. Values flow from inventory, `group_vars/`, play `vars`, role defaults, and command-line extra vars (`-e`). **Jinja2 templates** (`.j2` files) substitute variables into configuration files at deploy time on the control node before copying to targets.

This lab runs `playbooks/vars-demo.yml`, which renders `templates/motd.j2` to `/etc/motd` on every web server using `app_env` and `webserver_port` from `inventory/group_vars/webservers.yml`.

## Learning objectives

By the end of this lab you will be able to:

- Trace variables from `group_vars/webservers.yml` to running playbooks
- Read and modify a Jinja2 template (`motd.j2`)
- Use `ansible.builtin.template` to deploy rendered files
- Inspect merged variables with `ansible-inventory --host`
- Override variables at runtime with `-e` extra vars
- Explain basic variable precedence (extra vars > play vars > group_vars > defaults)
- Validate deployed file content on targets

## Prerequisites

- [ ] [Lab 04 — Apache playbook](lab04-playbook-apache-webserver.md) complete (Apache optional but recommended)
- [ ] `inventory/hosts.ini.local` with `webservers` group
- [ ] `inventory/group_vars/webservers.yml` present in repository
- [ ] Working directory: `~/terraform-ansible-labs/ansible/essentials/labs`

## Exercise index

| Exercise | Topic | Anchor |
|----------|-------|--------|
| [1](#ex1) | Review variables and template source | `group_vars`, `motd.j2` |
| [2](#ex2) | Run vars-demo playbook | Template deployment |
| [3](#ex3) | Validate /etc/motd on targets | Content verification |
| [4](#ex4) | Variable inspection and overrides | `-e` and inventory |
| [5](#ex5) | Template change and idempotency | Edit loop |

## File reference

**`inventory/group_vars/webservers.yml`:**

```yaml
---
webserver_port: 80
app_env: production
```

**`templates/motd.j2`:**

```jinja2
Welcome to {{ inventory_hostname }}
Environment: {{ app_env }}
Web port: {{ webserver_port }}
```

**`playbooks/vars-demo.yml`:**

```yaml
---
- name: Deploy MOTD from template
  hosts: webservers
  become: true
  tasks:
    - name: Template motd
      ansible.builtin.template:
        src: ../templates/motd.j2
        dest: /etc/motd
        mode: "0644"
```

---

## Exercise 1 — Review variables and template source

<a id="ex1"></a>

### Step 1.1 — Change to labs directory

```bash
cd ~/terraform-ansible-labs/ansible/essentials/labs
```

**Validate**

```bash
ls playbooks/vars-demo.yml templates/motd.j2 inventory/group_vars/webservers.yml
```

All three files exist.

**What happened:** The playbook references template via relative path `../templates/motd.j2` from `playbooks/` directory.

### Step 1.2 — Display group variables

```bash
cat inventory/group_vars/webservers.yml
```

**Validate**

```yaml
webserver_port: 80
app_env: production
```

**What happened:** These keys become Jinja variables available to any play targeting `webservers` without explicit `vars:` in the playbook.

### Step 1.3 — Display the Jinja template

```bash
cat templates/motd.j2
```

**Validate** — three lines referencing `inventory_hostname`, `app_env`, and `webserver_port`.

**What happened:** `inventory_hostname` is a **magic variable** — Ansible sets it to the inventory name (`web1`, `web2`). Magic variables do not need to be defined in `group_vars`.

### Step 1.4 — Display the playbook

```bash
cat playbooks/vars-demo.yml
```

**Validate** — single task using `ansible.builtin.template` with `dest: /etc/motd` and `mode: "0644"`.

**What happened:** `become: true` is required because `/etc/motd` is root-owned. The template module renders on the **control node**, then transfers the result.

### Step 1.5 — Preview merged variables for web1

```bash
ansible-inventory -i inventory/hosts.ini.local --host web1
```

**Validate** — JSON includes:

```json
"app_env": "production",
"webserver_port": 80
```

**What happened:** This is the variable context available when the template renders for `web1`.

---

## Exercise 2 — Run vars-demo playbook

<a id="ex2"></a>

### Step 2.1 — Syntax-check

```bash
ansible-playbook --syntax-check playbooks/vars-demo.yml
```

**Validate** — no errors.

**What happened:** Catches YAML and path issues before SSH connections.

### Step 2.2 — Apply the playbook

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/vars-demo.yml
```

**Validate**

```text
PLAY RECAP *********************************************************************
web1   : ok=...   changed=...   unreachable=0   failed=0
web2   : ok=...   changed=...   unreachable=0   failed=0
```

`failed=0` on every host. Expect `changed=1` on first deploy per host.

**What happened:** `ansible.builtin.template` compares checksum of rendered content to destination file. First run creates or replaces `/etc/motd`; subsequent identical runs show `ok`.

### Step 2.3 — List tasks

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/vars-demo.yml --list-tasks
```

**Validate**

```text
Template motd
```

**What happened:** Single-task playbooks are common for focused configuration drops.

### Step 2.4 — Re-run immediately (idempotency preview)

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/vars-demo.yml
```

**Validate** — `changed=0` on template task.

**What happened:** Identical rendered content produces no change — safe to run in scheduled pipelines.

---

## Exercise 3 — Validate /etc/motd on targets

<a id="ex3"></a>

### Step 3.1 — Read MOTD on web1

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.command -a "cat /etc/motd"
```

**Validate**

```text
Welcome to web1
Environment: production
Web port: 80
```

(host name line shows `web1` specifically)

**What happened:** Template rendered per-host — `inventory_hostname` differs on `web2`.

### Step 3.2 — Read MOTD on web2

```bash
ansible web2 -i inventory/hosts.ini.local -m ansible.builtin.command -a "cat /etc/motd"
```

**Validate**

```text
Welcome to web2
Environment: production
Web port: 80
```

**What happened:** Same group variables, different host magic variable.

### Step 3.3 — Verify file permissions

```bash
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.command -a "ls -l /etc/motd"
```

**Validate**

```text
-rw-r--r-- ... /etc/motd
```

**What happened:** `mode: "0644"` in playbook sets world-readable, owner-writable — typical for MOTD.

### Step 3.4 — Confirm MOTD displays on SSH login (optional)

From control node:

```bash
ssh ubuntu@$(ansible-inventory -i inventory/hosts.ini.local --host web1 | grep ansible_host | awk -F'"' '{print $4}') 
```

**Validate** — login banner shows the three MOTD lines before shell prompt. Type `exit` to return.

**What happened:** `/etc/motd` is printed by pam_motd on Ubuntu SSH logins — confirms real-world effect beyond `cat`.

---

## Exercise 4 — Variable inspection and overrides

<a id="ex4"></a>

### Step 4.1 — Debug variables on webservers

```bash
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.debug -a "var=app_env"
```

**Validate** — `"app_env": "production"` on each host.

**What happened:** Same values the template consumed.

### Step 4.2 — Override app_env with extra vars

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/vars-demo.yml -e "app_env=staging"
```

**Validate** — playbook succeeds with `failed=0`.

**What happened:** `-e` extra vars have **highest precedence** in most scenarios — they override `group_vars` for this run only.

### Step 4.3 — Confirm staging value on disk

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.command -a "cat /etc/motd"
```

**Validate**

```text
Environment: staging
```

**What happened:** Demonstrates environment promotion pattern — same playbook, different `-e` or inventory per environment.

### Step 4.4 — Restore production value

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/vars-demo.yml
```

**Validate** — MOTD shows `Environment: production` again.

**What happened:** Without `-e`, group_vars values apply.

### Step 4.5 — Override webserver_port for one run

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/vars-demo.yml -e "webserver_port=8080"
```

**Validate**

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.command -a "grep 'Web port' /etc/motd"
```

```text
Web port: 8080
```

**What happened:** Variables are decoupled from template structure — change values without editing `.j2` files.

### Step 4.6 — Restore production port

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/vars-demo.yml
```

**Validate** — `Web port: 80`.

---

## Exercise 5 — Template change and idempotency

<a id="ex5"></a>

### Step 5.1 — Backup original template

```bash
cp templates/motd.j2 templates/motd.j2.bak
```

**Validate**

```bash
diff templates/motd.j2 templates/motd.j2.bak
```

No output (files identical).

**What happened:** Always backup before editing curriculum files; restore after lab.

### Step 5.2 — Add a line to the template

```bash
nano templates/motd.j2
```

Add a fourth line:

```jinja2
Managed by Ansible Essentials lab05
```

Save and exit.

**Validate**

```bash
tail -1 templates/motd.j2
```

```text
Managed by Ansible Essentials lab05
```

**What happened:** Any template content change alters rendered checksum — next playbook run should report `changed`.

### Step 5.3 — Apply playbook after template edit

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/vars-demo.yml
```

**Validate** — `changed=1` on template task for each host.

**What happened:** Template module detects drift between desired and actual file content.

### Step 5.4 — Verify new line on web1

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.command -a "cat /etc/motd"
```

**Validate** — includes `Managed by Ansible Essentials lab05`.

### Step 5.5 — Restore original template

```bash
mv templates/motd.j2.bak templates/motd.j2
```

**Validate**

```bash
wc -l templates/motd.j2
```

```text
3 templates/motd.j2
```

**What happened:** Restore repository state so lab 06+ match documentation. Re-run playbook if you want MOTD without the extra line:

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/vars-demo.yml
```

### Step 5.6 — Review interactive variables diagram

Open in browser:

- [Variables and templates](../html/variables-templates.html)

**Validate** — you can draw the path: `group_vars` → playbook → Jinja → `/etc/motd`.

---

## Key takeaways

- `group_vars/<group>.yml` supplies tier-wide values without duplicating per host
- Jinja2 `{{ variable }}` syntax renders on the control node inside `ansible.builtin.template`
- Magic variables like `inventory_hostname` are always available
- Extra vars (`-e`) override inventory for one-shot environment switches
- Template task idempotency is based on content checksum, not timestamps
- Relative `src: ../templates/motd.j2` resolves from playbook file location

## Done when

- [ ] `ansible-playbook` run of `vars-demo.yml` completes with `failed=0`
- [ ] `/etc/motd` on web1 shows correct `inventory_hostname`, `app_env`, and `webserver_port`
- [ ] `-e app_env=staging` changes deployed content; restored to `production`
- [ ] `ansible-inventory --host web1` shows merged group variables
- [ ] Template file restored to 3 lines if you edited it in exercise 5

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Undefined variable in template | Host not in `webservers` | Verify inventory group membership |
| `src` not found | Wrong working directory | Run from `labs/`; check `../templates/` path |
| Permission denied on `/etc/motd` | Missing `become: true` | Confirm playbook has `become: true` |
| Old content after override | Cached SSH session | Re-run playbook; `cat /etc/motd` directly |
| Extra var ignored | Typo in `-e` | Use exact key name: `app_env` not `app_environment` |
| Template syntax error | Invalid Jinja | Check `{{ }}` braces and variable names |

## Cleanup

Remove deployed MOTD (optional):

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.file -a "path=/etc/motd state=absent"
```

Restore default Ubuntu MOTD if desired:

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.apt -a "name=motd-news-config state=present"
```

**Validate** — `/etc/motd` absent or default package restored.

For lab 06, leaving MOTD in place is fine.

## Reference links

- [Ansible variables](../docs/05-variables/ansible-variables.md)
- [Interactive variables and templates](../html/variables-templates.html)
- [Template module](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/template_module.html)
- [Variable precedence](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable)

## Next steps

- [Lab 06 — Ansible roles](lab06-roles-create.md)
- [Lab manual index](README.md)

---
*Source: Ansible Essentials bootcamp · Lesson 5 AP-02 · Next: [lab06](lab06-roles-create.md)*
