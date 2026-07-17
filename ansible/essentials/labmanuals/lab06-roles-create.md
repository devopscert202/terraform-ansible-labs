# Lab 06: Ansible Roles

> **Goal:** Package web server automation into a reusable role and invoke it from a thin playbook — the standard pattern for production Ansible projects.
> **Time:** ~75 min · **Difficulty:** Intermediate · **Files:** `labs/roles/webserver/`, `labs/playbooks/role-site.yml`

## Overview

A **role** bundles tasks, handlers, defaults, templates, and files into a conventional directory tree. Playbooks stay short — they declare **which roles** to apply instead of repeating task blocks. Teams share roles via Git submodules, private Galaxy servers, or `ansible-galaxy install`.

This lab inspects the provided `webserver` role, compares it to `playbooks/apache.yml` from lab 04, and applies `playbooks/role-site.yml` which lists `roles: [webserver]`.

## Learning objectives

By the end of this lab you will be able to:

- Navigate the standard role directory layout (`tasks/`, `handlers/`, `defaults/`)
- Explain how role `defaults/main.yml` provides low-precedence variables
- Trace handler notification from role tasks to `handlers/main.yml`
- Run a playbook that invokes a role via the `roles:` keyword
- Compare monolithic playbooks versus role composition
- Use `ansible-galaxy init` to scaffold new roles (demonstration)
- Verify Apache service state after role application

## Prerequisites

- [ ] [Lab 05 — Variables and templates](lab05-playbook-variables.md) complete
- [ ] `inventory/hosts.ini.local` with working `webservers` group
- [ ] `ansible.cfg` sets `roles_path = roles` in `labs/`
- [ ] Working directory: `~/terraform-ansible-labs/ansible/essentials/labs`

## Exercise index

| Exercise | Topic | Anchor |
|----------|-------|--------|
| [1](#ex1) | Role directory anatomy | `roles/webserver/` |
| [2](#ex2) | Compare role tasks to apache.yml | Design patterns |
| [3](#ex3) | Run role-site playbook | Role execution |
| [4](#ex4) | Override role defaults | Variable injection |
| [5](#ex5) | Scaffold roles with ansible-galaxy | Role creation |

## Role reference

**`roles/webserver/defaults/main.yml`:**

```yaml
---
web_package: apache2
web_service: apache2
```

**`roles/webserver/tasks/main.yml`:**

```yaml
---
- name: Install web package
  ansible.builtin.apt:
    name: "{{ web_package }}"
    state: present
    update_cache: true

- name: Enable mod_rewrite
  ansible.builtin.apache2_module:
    name: rewrite
    state: present
  notify: Restart web service

- name: Ensure web service running
  ansible.builtin.service:
    name: "{{ web_service }}"
    state: started
    enabled: true
```

**`roles/webserver/handlers/main.yml`:**

```yaml
---
- name: Restart web service
  ansible.builtin.service:
    name: "{{ web_service }}"
    state: restarted
```

**`playbooks/role-site.yml`:**

```yaml
---
- name: Site with webserver role
  hosts: webservers
  become: true
  roles:
    - webserver
```

---

## Exercise 1 — Role directory anatomy

<a id="ex1"></a>

### Step 1.1 — Change to labs directory

```bash
cd ~/terraform-ansible-labs/ansible/essentials/labs
```

**Validate**

```bash
grep roles_path ansible.cfg
```

```text
roles_path = roles
```

**What happened:** Ansible searches `roles/webserver/` when a playbook lists `roles: - webserver`.

### Step 1.2 — List role files

```bash
find roles/webserver -type f | sort
```

**Validate**

```text
roles/webserver/defaults/main.yml
roles/webserver/handlers/main.yml
roles/webserver/tasks/main.yml
```

**What happened:** Standard role skeleton. Optional directories (`templates/`, `files/`, `vars/`, `meta/`) are not used in this minimal role but are available for larger designs.

### Step 1.3 — Read defaults

```bash
cat roles/webserver/defaults/main.yml
```

**Validate** — `web_package: apache2` and `web_service: apache2`.

**What happened:** **Defaults** have the lowest variable precedence — easy to override in playbooks, inventory, or `-e` without editing the role.

### Step 1.4 — Read tasks

```bash
cat roles/webserver/tasks/main.yml
```

**Validate** — three tasks: apt install, apache2_module, service ensure.

**What happened:** `tasks/main.yml` is the entry point Ansible loads automatically. No `import_tasks` needed for the default layout.

### Step 1.5 — Read handlers

```bash
cat roles/webserver/handlers/main.yml
```

**Validate** — handler named `Restart web service` uses `{{ web_service }}`.

**What happened:** Handler names must match `notify:` strings exactly. Role handlers merge into the play's handler list at runtime.

---

## Exercise 2 — Compare role tasks to apache.yml

<a id="ex2"></a>

### Step 2.1 — Display apache playbook from lab 04

```bash
cat playbooks/apache.yml
```

**Validate** — two tasks + handler; no explicit `service: started` task.

**What happened:** The role adds **ensure running and enabled** — stronger desired state than lab 04 alone.

### Step 2.2 — Side-by-side diff concept

Compare notify strings:

```bash
grep notify playbooks/apache.yml roles/webserver/tasks/main.yml
```

**Validate**

```text
playbooks/apache.yml:      notify: Restart apache2
roles/webserver/tasks/main.yml:  notify: Restart web service
```

**What happened:** Handler names are role-internal strings — the role uses parameterized `web_service` variable for portability (could switch to `nginx` with overrides).

### Step 2.3 — Confirm role uses variables in tasks

```bash
grep '{{' roles/webserver/tasks/main.yml
```

**Validate** — `{{ web_package }}` and `{{ web_service }}` appear.

**What happened:** Parameterized roles support multiple distributions or web servers without forking task code.

### Step 2.4 — Review interactive roles diagram

Open in browser:

- [Roles and Vault overview](../html/roles-and-vault.html)

**Validate** — you understand roles encapsulate tasks + handlers + defaults.

---

## Exercise 3 — Run role-site playbook

<a id="ex3"></a>

### Step 3.1 — Syntax-check role-site playbook

```bash
ansible-playbook --syntax-check playbooks/role-site.yml
```

**Validate** — no errors.

**What happened:** Syntax check resolves role paths using `roles_path` from `ansible.cfg`.

### Step 3.2 — List tasks including role tasks

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/role-site.yml --list-tasks
```

**Validate**

```text
webserver : Install web package
webserver : Enable mod_rewrite
webserver : Ensure web service running
```

Role name prefix appears in task listing.

**What happened:** Ansible expands roles into the play's task list at compile time.

### Step 3.3 — Apply the playbook

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/role-site.yml
```

**Validate**

```text
PLAY RECAP *********************************************************************
web1   : ok=...   changed=...   unreachable=0   failed=0
web2   : ok=...   changed=...   unreachable=0   failed=0
```

`failed=0` on every host.

**What happened:** Even if lab 04 already installed Apache, the role ensures service enabled/running and may report `ok` with `changed=0` on second application.

### Step 3.4 — Verify Apache active on webservers

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.command -a "systemctl is-active apache2"
```

**Validate**

```text
active
```

on each host.

**What happened:** Role's third task explicitly ensures service state — production roles should not assume install implies running.

### Step 3.5 — Verify mod_rewrite

```bash
ansible web1 -i inventory/hosts.ini.local -b -m ansible.builtin.command -a "apache2ctl -M | grep rewrite"
```

**Validate** — `rewrite_module` present.

### Step 3.6 — Re-run for idempotency

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/role-site.yml
```

**Validate** — `changed=0` on all role tasks; no handler unless module reported change.

---

## Exercise 4 — Override role defaults

<a id="ex4"></a>

### Step 4.1 — Show effective variables during role (debug play)

Create a temporary inline check using ad hoc with ansible facts — or inspect defaults:

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.debug -a "msg=package={{ web_package | default('undefined') }}"
```

**Validate** — may show `undefined` in ad hoc without role context. Instead, use playbook vars:

**What happened:** Role defaults apply inside plays that include the role. Demonstrate override with `roles` + `vars`:

### Step 4.2 — Run with inline role parameters (Ansible 2.8+ style)

Edit is not required — run this one-liner playbook via command line using `--extra-vars` at play level is complex; instead override via inventory `group_vars`:

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/role-site.yml -e "web_package=apache2"
```

**Validate** — succeeds (same package — demonstrates `-e` reaches role tasks).

**What happened:** Extra vars override role defaults. To simulate nginx you would set `web_package=nginx` **only on hosts with nginx packages available** — not part of this Ubuntu Apache lab.

### Step 4.3 — Document precedence for this lab

Answer:

1. Where are `web_package` and `web_service` defined?
2. What would override them?

**Validate** — defaults in `roles/webserver/defaults/main.yml`; overridden by inventory, play `vars`, or `-e`.

### Step 4.4 — List role handlers

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/role-site.yml --list-handlers
```

**Validate**

```text
webserver : Restart web service
```

**What happened:** Handlers are scoped to the role but execute in play context.

---

## Exercise 5 — Scaffold roles with ansible-galaxy

<a id="ex5"></a>

### Step 5.1 — View galaxy init help

```bash
ansible-galaxy role init --help | head -20
```

**Validate** — help text displays.

**What happened:** `ansible-galaxy role init` scaffolds the standard directory tree — same structure as `roles/webserver/`.

### Step 5.2 — Initialize a throwaway role in /tmp

```bash
mkdir -p /tmp/ansible-role-lab && cd /tmp/ansible-role-lab
ansible-galaxy role init demo_role
```

**Validate**

```bash
find demo_role -type f | sort
```

Shows `defaults`, `handlers`, `tasks`, `meta`, `tests`, etc.

**What happened:** Generated skeleton matches Ansible best practices. Production teams commit scaffolded roles and fill in tasks.

### Step 5.3 — Return to labs directory

```bash
cd ~/terraform-ansible-labs/ansible/essentials/labs
```

**Validate**

```bash
pwd
```

ends with `ansible/essentials/labs`.

### Step 5.4 — Remove throwaway role

```bash
rm -rf /tmp/ansible-role-lab
```

**What happened:** Keep lab environment clean. The curriculum role remains at `roles/webserver/`.

### Step 5.5 — Role versus playbook decision checklist

| Use a role when | Use inline tasks when |
|-----------------|----------------------|
| Logic is reused across playbooks | One-off prototype |
| Team shares automation via Galaxy/Git | Single play, never repeated |
| Defaults should be overridable | Experiment before extracting |

**Validate** — you would refactor lab 04's `apache.yml` into this role for a real project.

---

## Key takeaways

- Roles live under `roles_path` (`roles/` in this lab)
- `defaults/main.yml` → `tasks/main.yml` → `handlers/main.yml` is the core trio
- Playbooks invoke roles with `roles: - rolename` under a play
- Role tasks appear prefixed in `--list-tasks` output
- Handlers inside roles follow the same notify semantics as play-level handlers
- `ansible-galaxy role init` scaffolds new roles with standard layout
- The `webserver` role supersedes lab 04 with explicit service ensure task

## Done when

- [ ] `find roles/webserver` shows tasks, handlers, defaults
- [ ] `ansible-playbook playbooks/role-site.yml` completes with `failed=0`
- [ ] `systemctl is-active apache2` returns `active` on all webservers
- [ ] Second playbook run shows `changed=0`
- [ ] You can explain role defaults versus group_vars precedence
- [ ] You ran `ansible-galaxy role init` demonstration in /tmp

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Role not found | Wrong `roles_path` or cwd | Run from `labs/`; verify `ansible.cfg` |
| Handler not running | Task not `changed` | Normal on idempotent re-run |
| Variable undefined in role | Typo in defaults | Check `defaults/main.yml` keys |
| apt install wrong package | Bad `-e` override | Remove override; use `apache2` |
| Permission denied | Missing `become` | `role-site.yml` has `become: true` |
| Duplicate handler errors | Name collision | Keep handler names unique per play |

## Cleanup

Same as lab 04 if removing Apache entirely:

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.apt -a "name=apache2 state=absent purge=true autoremove=yes"
```

For lab 07, **keep Apache and webservers running** — only Node.js is added in the capstone.

## Reference links

- [Ansible roles](../docs/06-roles/ansible-roles.md)
- [Interactive roles and Vault](../html/roles-and-vault.html)
- [Roles documentation](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_reuse_roles.html)
- [ansible-galaxy](https://docs.ansible.com/ansible/latest/galaxy/user_guide.html)

## Next steps

- [Lab 07 — Vault and Node.js capstone](lab07-vault-and-nodejs-capstone.md)
- [Lab manual index](README.md)

---
*Source: Ansible Essentials bootcamp · Lesson 6 AP-01 · Next: [lab07](lab07-vault-and-nodejs-capstone.md)*
