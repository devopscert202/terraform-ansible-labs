# Lab 02: Hosts and Groups

> **Goal:** Organize servers into groups, compare INI and YAML inventory formats, and attach group variables that Ansible merges automatically.
> **Time:** ~60 min · **Difficulty:** Beginner · **Files:** `labs/inventory/hosts.yaml`, `labs/inventory/group_vars/webservers.yml`

## Overview

Inventory is more than a flat list of IPs. **Groups** let you target logical tiers (`webservers`, `dbservers`) and attach **variables** that every member inherits. In this lab you work with the repository's YAML inventory, inspect the group hierarchy with `ansible-inventory`, and prove that `group_vars/webservers.yml` values appear on every web host.

You will continue using `hosts.ini.local` for playbooks in later labs, but understanding YAML inventory and `group_vars/` is essential for real-world Ansible projects.

## Learning objectives

By the end of this lab you will be able to:

- Read and edit YAML inventory with nested `children` and `hosts`
- Compare INI (`hosts.ini`) and YAML (`hosts.yaml`) representations of the same fleet
- Use `ansible-inventory --graph` and `--host` to visualize groups and merged variables
- Explain how `inventory/group_vars/<group>.yml` applies variables to a group
- Run ad hoc `ansible.builtin.debug` to display group variables on targets
- Target subsets of inventory with host patterns (`webservers`, `dbservers`, `web1`)

## Prerequisites

- [ ] [Lab 01 — Static host inventory](lab01-inventory-static-hosts.md) complete
- [ ] `inventory/hosts.ini.local` exists with working connectivity to `web1` and `web2`
- [ ] Working directory: `~/terraform-ansible-labs/ansible/essentials/labs`

## Exercise index

| Exercise | Topic | Anchor |
|----------|-------|--------|
| [1](#ex1) | Review YAML inventory structure | `hosts.yaml` |
| [2](#ex2) | Visualize groups with ansible-inventory | `--graph`, `--list` |
| [3](#ex3) | Group variables from group_vars/ | `webservers.yml` |
| [4](#ex4) | Compare INI and YAML inventories | Format equivalence |
| [5](#ex5) | Host patterns and dbservers group | Multi-group targeting |

## What you will use

```
inventory/
├── hosts.ini              # INI format (committed sample)
├── hosts.yaml             # YAML format (same logical structure)
├── hosts.ini.local        # Your personal INI (from lab 01)
└── group_vars/
    └── webservers.yml     # webserver_port: 80, app_env: production
```

---

## Exercise 1 — Review YAML inventory structure

<a id="ex1"></a>

### Step 1.1 — Change to the labs directory

```bash
cd ~/terraform-ansible-labs/ansible/essentials/labs
pwd
```

**Validate**

```text
.../ansible/essentials/labs
```

**What happened:** All inventory commands in this lab run from `labs/` so relative paths in `ansible.cfg` resolve correctly.

### Step 1.2 — Display the YAML inventory

```bash
cat inventory/hosts.yaml
```

**Validate** — structure matches:

```yaml
all:
  children:
    webservers:
      hosts:
        web1:
          ansible_host: 10.0.1.10
          ansible_user: ubuntu
        web2:
          ansible_host: 10.0.1.11
          ansible_user: ubuntu
      vars:
        ansible_python_interpreter: /usr/bin/python3
    dbservers:
      hosts:
        db1:
          ansible_host: 10.0.1.20
          ansible_user: ubuntu
```

**What happened:** YAML inventory nests groups under `all.children`. Host-level variables sit under each host key. Group-level variables (like `ansible_python_interpreter`) sit under `vars` for that group — equivalent to `[webservers:vars]` in INI format.

### Step 1.3 — Update IPs in hosts.yaml for your environment (optional)

If you want YAML inventory to match your AWS private IPs:

```bash
nano inventory/hosts.yaml
```

Replace `10.0.1.10`, `10.0.1.11`, and `10.0.1.20` with your real addresses. Save and exit.

**Validate**

```bash
grep ansible_host inventory/hosts.yaml
```

Shows your IPs (or placeholders if you skip this step).

**What happened:** Committed files use curriculum placeholders. For connectivity tests with `hosts.yaml`, IPs must be reachable. Playbooks in labs 03–07 use `hosts.ini.local` instead — you only need to update `hosts.yaml` if you run commands against it in this lab.

### Step 1.4 — Parse YAML inventory without connecting

```bash
ansible-inventory -i inventory/hosts.yaml --list > /dev/null && echo "YAML inventory OK"
```

**Validate**

```text
YAML inventory OK
```

**What happened:** `ansible-inventory` validates structure before any SSH connection. YAML indentation errors are a common failure mode — use spaces, not tabs.

---

## Exercise 2 — Visualize groups with ansible-inventory

<a id="ex2"></a>

### Step 2.1 — Show inventory graph

```bash
ansible-inventory -i inventory/hosts.yaml --graph
```

**Validate**

```text
@all:
  |--@ungrouped:
  |--@webservers:
  |  |--web1
  |  |--web2
  |--@dbservers:
  |  |--db1
```

**What happened:** The graph shows parent/child relationships. `@` prefixes denote groups. `ungrouped` is empty when every host belongs to at least one group. This view is invaluable when inventory grows beyond a handful of hosts.

### Step 2.2 — List all hosts in YAML format

```bash
ansible-inventory -i inventory/hosts.yaml --list-hosts
```

**Validate**

```text
  hosts (3):
    web1
    web2
    db1
```

**What happened:** Three hosts across two groups. If `db1` is not provisioned in your AWS lab, note that ping tests against `all` may include an unreachable host — use group-scoped patterns when needed.

### Step 2.3 — Show merged variables for web1

```bash
ansible-inventory -i inventory/hosts.yaml --host web1
```

**Validate** — JSON includes at minimum:

```json
"ansible_host": "10.0.1.10",
"ansible_user": "ubuntu",
"ansible_python_interpreter": "/usr/bin/python3",
"app_env": "production",
"webserver_port": 80
```

**What happened:** Variables from three sources merge: host keys in `hosts.yaml`, group `vars` in `hosts.yaml`, and files in `inventory/group_vars/webservers.yml`. Ansible loads `group_vars` automatically when the directory sits beside the inventory file or in a `group_vars/` tree relative to the inventory path.

### Step 2.4 — List only webservers group

```bash
ansible-inventory -i inventory/hosts.yaml webservers --list-hosts
```

**Validate**

```text
  hosts (2):
    web1
    web2
```

**What happened:** Passing a pattern to `ansible-inventory` filters output the same way the `ansible` command filters execution targets.

---

## Exercise 3 — Group variables from group_vars/

<a id="ex3"></a>

### Step 3.1 — Read group_vars file

```bash
cat inventory/group_vars/webservers.yml
```

**Validate**

```yaml
---
webserver_port: 80
app_env: production
```

**What happened:** File name `webservers.yml` matches group name `webservers`. Every host in that group receives `webserver_port` and `app_env` without repeating them on each host line. This is the DRY (Don't Repeat Yourself) pattern for environment-wide settings.

### Step 3.2 — Debug webserver_port on all web servers

Use your personal INI inventory (real IPs) for connectivity:

```bash
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.debug -a "var=webserver_port"
```

**Validate**

```text
web1 | SUCCESS => {
    "webserver_port": 80
}
web2 | SUCCESS => {
    "webserver_port": 80
}
```

**What happened:** `ansible.builtin.debug` prints a variable value on each host. Ansible merged `group_vars/webservers.yml` even though you passed INI inventory — `group_vars/` is resolved relative to the inventory directory.

### Step 3.3 — Debug app_env on web1 only

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.debug -a "var=app_env"
```

**Validate**

```text
"app_env": "production"
```

**What happened:** String values appear quoted in JSON output. The same variable will be consumed by Jinja templates in lab 05.

### Step 3.4 — Debug multiple variables with a message

```bash
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.debug -a "msg=Host {{ inventory_hostname }} env={{ app_env }} port={{ webserver_port }}"
```

**Validate** — each host prints a line containing `env=production` and `port=80`.

**What happened:** Jinja expressions work in ad hoc `-a` strings as well as in playbooks. `inventory_hostname` is a magic variable set to the inventory name (`web1`, `web2`).

### Step 3.5 — Confirm dbservers do not inherit webservers vars

If `db1` is in your `hosts.ini.local`:

```bash
ansible db1 -i inventory/hosts.ini.local -m ansible.builtin.debug -a "var=webserver_port"
```

**Validate** — either `VARIABLE IS NOT DEFINED` or the variable is absent unless you added dbservers to the same group_vars scope.

**What happened:** Group variables are scoped to their group. Database servers should not automatically receive web-tier settings unless you intentionally share a parent group or use `group_vars/all.yml`.

---

## Exercise 4 — Compare INI and YAML inventories

<a id="ex4"></a>

### Step 4.1 — Display INI inventory side by side

```bash
echo "=== INI ===" && cat inventory/hosts.ini && echo && echo "=== YAML ===" && cat inventory/hosts.yaml
```

**Validate** — both define `web1`, `web2`, `db1` with the same connection variables and `webservers` group vars for Python interpreter.

**What happened:** Teams pick one format per project. INI is compact for small inventories; YAML scales better with deep group nesting and inline structures. Ansible treats them equivalently once parsed.

### Step 4.2 — Graph INI inventory

```bash
ansible-inventory -i inventory/hosts.ini --graph
```

**Validate** — same group tree as YAML:

```text
@webservers:
  |--web1
  |--web2
@dbservers:
  |--db1
```

**What happened:** Parsing produces the same internal data model regardless of source format.

### Step 4.3 — Graph your personal INI inventory

```bash
ansible-inventory -i inventory/hosts.ini.local --graph
```

**Validate** — at minimum `webservers` with `web1` and `web2`; `dbservers` if configured.

**What happened:** Your personal file may omit `db1` if you have not provisioned a database node. That is fine for web-focused labs.

### Step 4.4 — Show host vars from personal inventory

```bash
ansible-inventory -i inventory/hosts.ini.local --host web2
```

**Validate** — includes `webserver_port: 80` and `app_env: production` from `group_vars/` plus your real `ansible_host`.

**What happened:** This is the merged view playbooks see at runtime. When a template references `{{ app_env }}`, this is where the value originates.

---

## Exercise 5 — Host patterns and dbservers group

<a id="ex5"></a>

### Step 5.1 — Ping webservers only

```bash
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.ping
```

**Validate** — `pong` on `web1` and `web2`.

**What happened:** Group patterns are the most common targeting mechanism in playbooks (`hosts: webservers`).

### Step 5.2 — Ping dbservers (if provisioned)

```bash
ansible dbservers -i inventory/hosts.ini.local -m ansible.builtin.ping
```

**Validate** — `pong` on `db1`, or skip if `db1` is not in your inventory.

**What happened:** Separating tiers into groups lets you run database tasks only against `dbservers` without touching web nodes.

### Step 5.3 — Add db1 to hosts.ini.local (if missing)

If your personal inventory lacks the database tier, edit it to match the repository sample:

```bash
nano inventory/hosts.ini.local
```

Add:

```ini
[dbservers]
db1 ansible_host=10.0.1.20 ansible_user=ubuntu
```

(use your real db private IP)

**Validate**

```bash
ansible-inventory -i inventory/hosts.ini.local --graph
```

Shows `@dbservers` with `db1`.

**What happened:** Inventory evolves with your infrastructure. Keeping personal inventory aligned with the curriculum sample reduces surprises in later labs.

### Step 5.4 — Union pattern webservers:dbservers

```bash
ansible 'webservers:dbservers' -i inventory/hosts.ini.local -m ansible.builtin.ping
```

**Validate** — `pong` on every host in either group.

**What happened:** Colon `:` means OR in Ansible patterns. You will use richer patterns (`&` for AND, `!` for exclusion) in advanced courses.

### Step 5.5 — Limit to one host within a group

```bash
ansible webservers -i inventory/hosts.ini.local -l web1 -m ansible.builtin.ping
```

**Validate** — only `web1` in output.

**What happened:** `--limit` (`-l`) restricts execution to a subset — critical for canary deploys and debugging one bad node.

---

## Key takeaways

- Groups organize hosts by role, environment, or region
- `group_vars/<groupname>.yml` applies variables to every member of that group
- INI and YAML inventory are interchangeable representations — pick one style per repo
- `ansible-inventory` inspects structure and merged variables without running tasks on targets
- Host patterns (`webservers`, `web1`, `all`, `webservers:dbservers`) control blast radius
- Variables from `group_vars/` merge with host-specific inventory keys automatically

## Done when

- [ ] `ansible-inventory -i inventory/hosts.yaml --graph` shows `webservers` and `dbservers`
- [ ] `ansible-inventory --host web1` shows `webserver_port: 80` and `app_env: production`
- [ ] `ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.debug -a "var=webserver_port"` returns `80` on each web host
- [ ] You can explain the difference between INI `[webservers:vars]` and `group_vars/webservers.yml`
- [ ] Personal `hosts.ini.local` includes at least `web1` and `web2` with working ping

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| YAML parse error | Bad indentation | Use 2 spaces; align `hosts:` under group name |
| Variable undefined | Host not in `webservers` group | Confirm host appears under `[webservers]` in INI |
| `group_vars` not applied | Inventory path wrong | Run from `labs/`; ensure `group_vars/` is beside inventory file |
| `--graph` missing db1 | db not in personal inventory | Add `[dbservers]` section or skip db exercises |
| `UNREACHABLE` on db1 only | DB node not provisioned | Remove `db1` from inventory or provision the instance |
| Different port value | Local override | Check for duplicate vars in `host_vars/` or inventory inline |

## Cleanup

No resources to destroy. Group variables and inventory files remain for lab 03.

```bash
# Optional verification
ansible-inventory -i inventory/hosts.ini.local --host web1 | grep -E 'app_env|webserver_port'
```

## Reference links

- [Inventory deep dive](../docs/02-inventory/inventory-ini-and-yaml.md)
- [Interactive inventory flow](../html/inventory-flow.html)
- [Group variables](https://docs.ansible.com/ansible/latest/inventory_guide/intro_inventory.html#organizing-host-and-group-variable-data)
- [Host patterns](https://docs.ansible.com/ansible/latest/inventory_guide/intro_patterns.html)

## Next steps

- [Lab 03 — Ad hoc commands](lab03-adhoc-commands.md)
- [Lab 01 — Static inventory](lab01-inventory-static-hosts.md) (review)
- [Interactive catalog](../html/index.html)

---
*Source: Ansible Essentials bootcamp · Lesson 2 AP-02 · Next: [lab03](lab03-adhoc-commands.md)*
