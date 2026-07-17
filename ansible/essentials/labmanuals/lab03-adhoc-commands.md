# Lab 03: Ad Hoc Commands

> **Goal:** Run one-off Ansible modules on multiple hosts from the CLI — no playbook required — and know when ad hoc is appropriate versus playbooks.
> **Time:** ~60 min · **Difficulty:** Beginner · **Files:** none (commands only; uses `inventory/hosts.ini.local`)

## Overview

Ad hoc commands execute a **single module** against a host pattern from the command line. They are ideal for quick checks (uptime, disk space, service status), exploratory package installs, and troubleshooting before you codify tasks into playbooks.

The `ansible` CLI reads inventory, connects via SSH on port 22, and runs modules using **FQCN** syntax such as `ansible.builtin.command`. This lab exercises the modules you will see again inside playbooks in labs 04–07.

## Learning objectives

By the end of this lab you will be able to:

- Construct ad hoc commands with `-m`, `-a`, `-i`, `-b`, and `-l`
- Choose between `ansible.builtin.command` and `ansible.builtin.shell`
- Install packages with `ansible.builtin.apt` using privilege escalation (`-b`)
- Gather facts with `ansible.builtin.setup` and filter output
- Use `ansible.builtin.service` and `ansible.builtin.file` for quick state checks
- Explain when ad hoc is sufficient versus when a playbook is required
- Clean up lab changes on targets

## Prerequisites

- [ ] [Lab 02 — Hosts and groups](lab02-inventory-hosts-groups.md) complete
- [ ] `inventory/hosts.ini.local` with working `ansible.builtin.ping` to `webservers`
- [ ] Ubuntu 22.04 targets with passwordless sudo for `ubuntu` user
- [ ] Working directory: `~/terraform-ansible-labs/ansible/essentials/labs`

## Exercise index

| Exercise | Topic | Anchor |
|----------|-------|--------|
| [1](#ex1) | Command module and uptime | Read-only ops |
| [2](#ex2) | Privilege escalation and apt | Package install |
| [3](#ex3) | Facts with setup module | Discovery |
| [4](#ex4) | Service and file modules | State inspection |
| [5](#ex5) | Limits, forks, and check mode | Safe execution |

---

## Exercise 1 — Command module and uptime

<a id="ex1"></a>

### Step 1.1 — Change to labs directory

```bash
cd ~/terraform-ansible-labs/ansible/essentials/labs
```

**Validate**

```bash
test -f inventory/hosts.ini.local && echo "Inventory ready"
```

```text
Inventory ready
```

**What happened:** All ad hoc commands in this lab use `-i inventory/hosts.ini.local` for your real IPs.

### Step 1.2 — Check uptime on all web servers

```bash
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.command -a "uptime"
```

**Validate**

```text
web1 | CHANGED | rc=0 >>
 web1 |  ... up ...
web2 | CHANGED | rc=0 >>
 web2 |  ... up ...
```

`rc=0` on each host; load averages and uptime string visible.

**What happened:** `ansible.builtin.command` runs a command without shell features (no pipes, redirects, or `&&`). It is the safe default when you do not need shell interpretation. `CHANGED` here means the module executed — not that the system changed.

### Step 1.3 — Run hostname on a single host

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.command -a "hostname"
```

**Validate**

```text
web1 | CHANGED | rc=0 >>
ip-10-0-1-xx
```

**What happened:** Narrow patterns reduce scope. Use single-host commands when debugging before applying changes fleet-wide.

### Step 1.4 — Use shell module for a pipeline (when needed)

```bash
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.shell -a "df -h / | tail -1"
```

**Validate** — each host shows root filesystem usage line with `rc=0`.

**What happened:** `ansible.builtin.shell` invokes `/bin/sh` and allows pipes. Prefer `command` unless you need shell syntax — shell injection risk is higher.

### Step 1.5 — Re-ping to confirm connectivity baseline

```bash
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.ping
```

**Validate** — `"ping": "pong"` on all web hosts.

**What happened:** Quick connectivity check before privileged operations in the next exercise.

---

## Exercise 2 — Privilege escalation and apt

<a id="ex2"></a>

### Step 2.1 — Attempt package query without become (expect failure or incomplete data)

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.command -a "dpkg -l tree"
```

**Validate** — may show `rc=1` or empty package list if `tree` is not installed.

**What happened:** Installing packages requires root. Without `-b` (become), Ansible runs as `ubuntu` and cannot write to system package directories.

### Step 2.2 — Install tree on web1 with apt module

```bash
ansible web1 -i inventory/hosts.ini.local -b -m ansible.builtin.apt -a "name=tree state=present update_cache=yes"
```

**Validate**

```text
web1 | CHANGED => {
    ...
    "changed": true,
```

or `"changed": false` if already installed.

**What happened:** `-b` enables privilege escalation using `become_method = sudo` from `ansible.cfg`. `ansible.builtin.apt` is idempotent — `state=present` ensures the package exists without reinstalling every time. `update_cache=yes` refreshes apt metadata first.

### Step 2.3 — Verify tree binary exists

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.command -a "which tree"
```

**Validate**

```text
/usr/bin/tree
```

**What happened:** Confirms the package installed to a path on `$PATH`.

### Step 2.4 — Run tree as a quick demo

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.command -a "tree -L 1 /var/www"
```

**Validate** — directory listing or "command not found" if `/var/www` is empty; `rc=0` if path exists.

**What happened:** Ad hoc commands are useful for post-change validation before you write playbook tasks.

### Step 2.5 — Install tree on entire webservers group

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.apt -a "name=tree state=present"
```

**Validate** — `SUCCESS` or `CHANGED` on `web1` and `web2`; no `FAILED`.

**What happened:** Same module, wider pattern — this is how you would patch a package across a tier. In production, codify this in a playbook under version control.

---

## Exercise 3 — Facts with setup module

<a id="ex3"></a>

### Step 3.1 — Gather all facts on web1 (verbose)

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.setup
```

**Validate** — large JSON blob with `"ansible_facts"` containing `ansible_hostname`, `ansible_memtotal_mb`, `ansible_distribution`, etc.

**What happened:** The setup module collects **facts** about the target — OS, hardware, network interfaces, mounts. Playbooks gather facts by default unless `gather_facts: false`.

### Step 3.2 — Filter facts to distribution only

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.setup -a "filter=ansible_distribution*"
```

**Validate**

```json
"ansible_distribution": "Ubuntu",
"ansible_distribution_version": "22.04",
"ansible_distribution_release": "jammy",
```

**What happened:** Filters reduce noise. Use fact names as Jinja variables in playbooks (`{{ ansible_distribution }}`).

### Step 3.3 — Debug a fact via command

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.debug -a "msg=OS is {{ ansible_distribution }}"
```

**Validate** — may show `OS is Ubuntu` **only if facts were gathered in the same play** — ad hoc does not persist facts between invocations.

**What happened:** In ad hoc mode, each command is independent. If the message shows undefined, run setup first or use `-m setup` then debug in one combined playbook. For ad hoc, query directly:

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.setup -a "filter=ansible_distribution" | grep ansible_distribution
```

**Validate** — line containing `"ansible_distribution": "Ubuntu"`.

### Step 3.4 — Gather memory fact on all webservers

```bash
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.setup -a "filter=ansible_memtotal_mb"
```

**Validate** — each host reports memory total in MB.

**What happened:** Fleet-wide fact gathering helps capacity planning and conditional tasks (`when: ansible_memtotal_mb > 4096`).

---

## Exercise 4 — Service and file modules

<a id="ex4"></a>

### Step 4.1 — Check if apache2 is installed (likely not yet)

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.command -a "systemctl is-active apache2"
```

**Validate** — `inactive` or `failed` with non-zero rc if Apache is not installed — expected before lab 04.

**What happened:** Baseline before the Apache playbook. `systemctl is-active` returns non-zero when the unit is not running.

### Step 4.2 — Ensure /tmp/ansible-lab-marker exists

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.file -a "path=/tmp/ansible-lab-marker state=touch mode=0644"
```

**Validate**

```text
"changed": true
```

on first run.

**What happened:** `ansible.builtin.file` manages file attributes and presence — idempotent alternative to `touch`.

### Step 4.3 — Verify marker file

```bash
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.command -a "ls -l /tmp/ansible-lab-marker"
```

**Validate**

```text
-rw-r--r-- ... /tmp/ansible-lab-marker
```

**What happened:** Read-only check as unprivileged user works because `/tmp` is world-readable.

### Step 4.4 — Copy local ansible.cfg content to targets (demonstration)

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.copy -a "src=ansible.cfg dest=/tmp/ansible.cfg mode=0644"
```

**Validate**

```text
web1 | CHANGED =>
```

**What happened:** `ansible.builtin.copy` transfers files from control node to targets. `src` is relative to the playbook directory or current working directory in ad hoc context. This pattern appears in configuration management playbooks.

### Step 4.5 — Read copied file back

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.command -a "head -3 /tmp/ansible.cfg"
```

**Validate**

```ini
[defaults]
inventory = inventory/hosts.ini
```

**What happened:** Confirms file transfer integrity.

---

## Exercise 5 — Limits, forks, and check mode

<a id="ex5"></a>

### Step 5.1 — Limit webservers group to web2 only

```bash
ansible webservers -i inventory/hosts.ini.local -l web2 -m ansible.builtin.command -a "hostname"
```

**Validate** — only `web2` appears in output.

**What happened:** `--limit` (`-l`) is essential for canary testing — run on one node before the fleet.

### Step 5.2 — Control parallelism with forks

```bash
ansible webservers -i inventory/hosts.ini.local -f 1 -m ansible.builtin.command -a "sleep 2; hostname"
```

**Validate** — hosts complete sequentially (slower than default `-f 5`).

**What happened:** `-f` sets simultaneous SSH sessions. Lower forks reduce load on fragile networks; higher forks speed large fleets.

### Step 5.3 — Dry-run apt with check mode

```bash
ansible web1 -i inventory/hosts.ini.local -b -C -m ansible.builtin.apt -a "name=htop state=present"
```

**Validate** — may report `changed` hypothetically or `ok` without actually installing.

**What happened:** `-C` (`--check`) asks modules to predict changes without applying them. Not all modules support check mode equally — apt generally does.

### Step 5.4 — Compare ad hoc versus playbook (conceptual)

Review what ad hoc cannot do:

- No `notify` / handlers
- No role composition
- No structured multi-task workflows in Git

Open the interactive reference in a browser on your workstation:

- [Ad hoc vs playbook](../html/adhoc-vs-playbook.html)

**Validate** — you understand ad hoc is for **ops and discovery**, playbooks for **repeatable automation**.

**What happened:** Lab 04 converts the Apache install from ad hoc style into a version-controlled playbook.

### Step 5.5 — Final fleet ping

```bash
ansible webservers -i inventory/hosts.ini.local -m ansible.builtin.ping
```

**Validate** — all `pong`.

---

## Key takeaways

- Syntax: `ansible <pattern> -i <inventory> -m <fqcn.module> [-a "args"] [-b]`
- Use `-b` when tasks require root (packages, services, most `/etc` changes)
- Prefer `ansible.builtin.command` over `shell` unless you need pipes or redirects
- `ansible.builtin.setup` discovers target attributes for conditional logic
- `--limit` restricts blast radius; `-C` dry-runs supported modules
- Ad hoc commands are not a substitute for playbooks in production

## Done when

- [ ] Uptime command succeeded on `webservers` with `rc=0`
- [ ] `tree` package installed on `web1` (and optionally entire group) using `-b` and `ansible.builtin.apt`
- [ ] `ansible.builtin.setup` shows `ansible_distribution: Ubuntu`
- [ ] Created `/tmp/ansible-lab-marker` with `ansible.builtin.file`
- [ ] Used `-l web2` successfully to limit execution
- [ ] Removed lab packages and temp files in cleanup (below)

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `sudo: a password is required` | Missing become or NOPASSWD | Add `-b`; verify sudoers for `ubuntu` |
| `Could not find apt` | Wrong OS family | Confirm Ubuntu targets; use `yum`/`dnf` on RHEL |
| `Failed to lock apt` | Concurrent apt process | Wait; stop unattended-upgrades; retry |
| `Permission denied` on file module | Missing `-b` | Add `-b` for paths outside user home |
| `template error` in debug | Facts not gathered | Run `setup` first or use playbook |
| `UNREACHABLE` | Inventory or SSH issue | Return to [lab01](lab01-inventory-static-hosts.md) |
| copy module src not found | Wrong working directory | Run from `labs/` directory |

## Cleanup

Remove lab packages and temporary files:

```bash
cd ~/terraform-ansible-labs/ansible/essentials/labs

ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.apt -a "name=tree state=absent autoremove=yes"

ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.file -a "path=/tmp/ansible-lab-marker state=absent"

ansible web1 -i inventory/hosts.ini.local -b -m ansible.builtin.file -a "path=/tmp/ansible.cfg state=absent"
```

**Validate** — `which tree` returns non-zero; marker and copied cfg removed.

## Reference links

- [Ad hoc commands deep dive](../docs/03-adhoc/adhoc-commands.md)
- [Interactive ad hoc vs playbook](../html/adhoc-vs-playbook.html)
- [Ansible command line documentation](https://docs.ansible.com/ansible/latest/command_guide/intro_adhoc.html)
- [Become (privilege escalation)](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_privilege_escalation.html)

## Next steps

- [Lab 04 — Apache playbook](lab04-playbook-apache-webserver.md)
- [Lab manual index](README.md)

---
*Source: Ansible Essentials bootcamp · Lesson 3 AP-01 · Next: [lab04](lab04-playbook-apache-webserver.md)*
