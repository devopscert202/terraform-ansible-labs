# Lab 04: Apache Playbook

> **Goal:** Install and configure Apache on all web servers using a playbook; observe handlers restart the service when configuration changes.
> **Time:** ~75 min · **Difficulty:** Intermediate · **Files:** `labs/playbooks/apache.yml`

## Overview

A **playbook** is a YAML file that describes desired state across a fleet. Unlike ad hoc commands, playbooks are version-controlled, reviewable, and support **handlers** — tasks that run only when notified, typically to restart services after config changes.

This lab walks through `playbooks/apache.yml`, which installs `apache2`, enables `mod_rewrite`, and restarts Apache via a handler when the module changes. You will validate service state, test idempotency, and inspect handler behavior.

## Learning objectives

By the end of this lab you will be able to:

- Read a playbook's `hosts`, `become`, `tasks`, `handlers`, and `notify` sections
- Run `ansible-playbook` with `-i inventory/hosts.ini.local`
- Use `ansible-playbook --syntax-check` before applying changes
- Interpret `PLAY RECAP` counters (`ok`, `changed`, `failed`)
- Verify Apache is active with ad hoc `ansible.builtin.command`
- Demonstrate idempotency by running the playbook twice
- Explain when handlers execute and why they batch at play end

## Prerequisites

- [ ] [Lab 03 — Ad hoc commands](lab03-adhoc-commands.md) complete
- [ ] `inventory/hosts.ini.local` with working connectivity to `webservers`
- [ ] Ubuntu 22.04 targets with passwordless sudo
- [ ] Working directory: `~/terraform-ansible-labs/ansible/essentials/labs`

## Exercise index

| Exercise | Topic | Anchor |
|----------|-------|--------|
| [1](#ex1) | Read and understand apache.yml | Playbook anatomy |
| [2](#ex2) | Syntax check and first apply | Initial deployment |
| [3](#ex3) | Verify Apache service and HTTP | Validation |
| [4](#ex4) | Idempotency and handler behavior | Second run |
| [5](#ex5) | Dry run and verbose troubleshooting | Safe iteration |

## Playbook reference

The repository ships this playbook at `playbooks/apache.yml`:

```yaml
---
- name: Install and configure Apache
  hosts: webservers
  become: true
  tasks:
    - name: Install apache2
      ansible.builtin.apt:
        name: apache2
        state: present
        update_cache: true

    - name: Enable mod_rewrite
      ansible.builtin.apache2_module:
        name: rewrite
        state: present
      notify: Restart apache2

  handlers:
    - name: Restart apache2
      ansible.builtin.service:
        name: apache2
        state: restarted
```

---

## Exercise 1 — Read and understand apache.yml

<a id="ex1"></a>

### Step 1.1 — Change to labs directory

```bash
cd ~/terraform-ansible-labs/ansible/essentials/labs
```

**Validate**

```bash
test -f playbooks/apache.yml && echo "Playbook found"
```

```text
Playbook found
```

**What happened:** Playbooks live under `playbooks/` relative to `labs/`. `ansible.cfg` sets `roles_path` but playbooks are invoked by explicit path.

### Step 1.2 — Display the playbook

```bash
cat playbooks/apache.yml
```

**Validate** — output matches the reference block above: two tasks, one handler, `hosts: webservers`, `become: true`.

**What happened:**

| Section | Purpose |
|---------|---------|
| `hosts: webservers` | Target pattern from inventory |
| `become: true` | Run tasks as root via sudo |
| `ansible.builtin.apt` | Install `apache2` package idempotently |
| `ansible.builtin.apache2_module` | Enable Apache module `rewrite` |
| `notify: Restart apache2` | Queue handler if module reports `changed` |
| `handlers` | Run once at end of play if notified |

### Step 1.3 — Confirm baseline — Apache not running yet

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.command -a "systemctl is-active apache2" || true
```

**Validate** — `inactive` or `failed` on hosts that have not run this playbook.

**What happened:** Establishes pre-playbook state for comparison after apply.

### Step 1.4 — Review interactive handler diagram (optional)

Open in a browser on your workstation:

- [Playbook execution and handlers](../html/playbook-handlers.html)

**Validate** — you can explain that handlers run **after** all tasks in the play complete.

---

## Exercise 2 — Syntax check and first apply

<a id="ex2"></a>

### Step 2.1 — Syntax-check the playbook

```bash
ansible-playbook --syntax-check playbooks/apache.yml
```

**Validate**

```text
playbook: playbooks/apache.yml
```

No syntax errors reported.

**What happened:** `--syntax-check` validates YAML structure and module argument names without connecting to hosts. Run this before every apply in CI pipelines.

### Step 2.2 — Apply the playbook

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/apache.yml
```

**Validate**

```text
PLAY RECAP *********************************************************************
web1   : ok=...   changed=...   unreachable=0   failed=0
web2   : ok=...   changed=...   unreachable=0   failed=0
```

`failed=0` on every host. Expect `changed` > 0 on first run for apt and possibly `apache2_module`.

**What happened:** Ansible connects to each host in `webservers`, escalates privileges, runs tasks in order, then runs notified handlers. `update_cache: true` on apt may take 30–60 seconds per host on first run.

### Step 2.3 — Review task output for handler notification

Scroll the output for lines like:

```text
TASK [Enable mod_rewrite] ***
changed: [web1]
...
RUNNING HANDLER [Restart apache2] ***
changed: [web1]
```

**Validate** — handler ran on hosts where `mod_rewrite` task reported `changed`.

**What happened:** If `mod_rewrite` was already enabled, the task may show `ok` and the handler might not run — both outcomes are valid on first run depending on image state.

### Step 2.4 — Count plays and tasks

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/apache.yml --list-tasks
```

**Validate**

```text
tasks:
  Install apache2
  Enable mod_rewrite
```

**What happened:** `--list-tasks` shows execution plan without running — useful for change review boards.

---

## Exercise 3 — Verify Apache service and HTTP

<a id="ex3"></a>

### Step 3.1 — Confirm service is active

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.command -a "systemctl is-active apache2"
```

**Validate**

```text
active
```

on each host.

**What happened:** `systemctl is-active` confirms the unit is running — stronger than checking package installation alone.

### Step 3.2 — Confirm service is enabled at boot

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.command -a "systemctl is-enabled apache2"
```

**Validate**

```text
enabled
```

**What happened:** The playbook's apt install enables the service on Debian-family systems; handler restart does not disable boot persistence.

### Step 3.3 — Check default index page locally on web1

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.command -a "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/"
```

**Validate**

```text
200
```

**What happened:** HTTP 200 from localhost confirms Apache serves the default Ubuntu page. External access may require security group rules on port 80 — not required for this lab.

### Step 3.4 — Verify mod_rewrite is enabled

```bash
ansible web1 -i inventory/hosts.ini.local -b -m ansible.builtin.command -a "apache2ctl -M"
```

**Validate** — output includes `rewrite_module`.

**What happened:** `ansible.builtin.apache2_module` enables the module and triggers the restart handler when it changes.

### Step 3.5 — List listening ports

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.command -a "ss -tlnp | grep apache2"
```

**Validate** — line showing `:80` or `*:80`.

**What happened:** Confirms Apache binds to port 80, matching `webserver_port: 80` in `group_vars/webservers.yml` used later in lab 05.

---

## Exercise 4 — Idempotency and handler behavior

<a id="ex4"></a>

### Step 4.1 — Re-run the playbook immediately

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/apache.yml
```

**Validate**

```text
PLAY RECAP *********************************************************************
web1   : ok=...   changed=0   unreachable=0   failed=0
web2   : ok=...   changed=0   unreachable=0   failed=0
```

`changed=0` for install and module tasks; **no** `RUNNING HANDLER` section.

**What happened:** Idempotent modules detect desired state already matches reality and report `ok` without changes. Handlers run only when a notifying task reports `changed`.

### Step 4.2 — List hosts the playbook would target

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/apache.yml --list-hosts
```

**Validate**

```text
  hosts (2):
    web1
    web2
```

**What happened:** Confirms `hosts: webservers` expands to your inventory members.

### Step 4.3 — Limit playbook to web1

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/apache.yml --limit web1
```

**Validate** — only `web1` in `PLAY RECAP`.

**What happened:** `--limit` works on playbooks the same as ad hoc commands — use for staged rollouts.

### Step 4.4 — Force handler thinking exercise (read-only)

Review the handler definition:

```bash
grep -A4 "handlers:" playbooks/apache.yml
```

**Validate** — handler uses `ansible.builtin.service` with `state: restarted`.

**What happened:** In production you might switch to `state: reloaded` for config-only changes to avoid dropping connections. Module enablement requires restart on Apache.

---

## Exercise 5 — Dry run and verbose troubleshooting

<a id="ex5"></a>

### Step 5.1 — Check mode dry run

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/apache.yml --check
```

**Validate** — tasks report `ok` or hypothetical `changed` without modifying targets (apt check mode support varies).

**What happened:** `--check` predicts changes. Combine with `--diff` in other playbooks to see file content deltas. Always verify check mode support per module in documentation.

### Step 5.2 — Verbose run on single host (optional)

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/apache.yml --limit web1 -vv
```

**Validate** — detailed SSH and module invocation logs.

**What happened:** Increase verbosity when `failed=1` and the summary is insufficient. `-vvv` shows connection plugin details.

### Step 5.3 — Document playbook purpose in your notes

Answer for yourself:

1. What triggers the handler?
2. Why is `become: true` at play level?
3. Why use FQCN `ansible.builtin.apt` instead of `apt`?

**Validate** — you can answer all three before lab 05.

**What happened:** Articulating design choices prepares you for code review and the variables lab.

### Step 5.4 — Compare to ad hoc equivalent (mental model)

The playbook replaces ad hoc:

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.apt -a "name=apache2 state=present update_cache=yes"
```

But adds handler orchestration impossible in a single ad hoc line.

---

## Key takeaways

- Playbooks declare **desired state**; idempotent modules make second runs safe
- `notify` + `handlers` decouple config changes from service restarts
- Handlers run **once** at play end per host, even if notified multiple times
- Always syntax-check before apply; use `--limit` for canary hosts
- `playbooks/apache.yml` uses FQCN modules required by Ansible 2.10+
- Apache on port 80 sets up labs 05–07 on the same web tier

## Done when

- [ ] `ansible-playbook --syntax-check playbooks/apache.yml` passes
- [ ] First playbook run completes with `failed=0` on all web hosts
- [ ] `systemctl is-active apache2` returns `active`
- [ ] `curl` to localhost returns HTTP `200`
- [ ] Second run shows `changed=0` and no handler execution
- [ ] You can explain handler trigger conditions

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `Permission denied` | Sudo not configured | Verify `become: true` and NOPASSWD for `ubuntu` |
| `Failed to lock apt` | Concurrent apt | Wait; stop other apt processes; retry |
| `apache2_module` not found | Missing collection | Use Ansible 2.14+ with `ansible.builtin.apache2_module` |
| Handler always runs | Task always `changed` | Check module state; review `-vv` output |
| `failed=1` on one host only | Partial deploy | Fix host; re-run with `--limit failed_host` |
| Playbook targets wrong hosts | Inventory mismatch | Confirm `-i inventory/hosts.ini.local` |
| YAML parse error | Indentation | Use spaces; validate with `--syntax-check` |

## Cleanup

Remove Apache if you want a clean slate before lab 06 (optional — lab 06 role also manages Apache):

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.apt -a "name=apache2 state=absent purge=true autoremove=yes"
```

**Validate**

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.command -a "systemctl is-active apache2" || true
```

Returns `inactive` or connection error for missing unit.

If continuing to lab 05, **skip cleanup** and keep Apache installed.

## Reference links

- [Playbooks and YAML basics](../docs/04-playbooks/playbook-and-yaml-basics.md)
- [Interactive playbook handlers](../html/playbook-handlers.html)
- [Ansible playbook guide](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_intro.html)
- [Handlers](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_handlers.html)

## Next steps

- [Lab 05 — Variables and templates](lab05-playbook-variables.md)
- [Lab manual index](README.md)

---
*Source: Ansible Essentials bootbook · Lesson 4 AP-01 · Next: [lab05](lab05-playbook-variables.md)*
