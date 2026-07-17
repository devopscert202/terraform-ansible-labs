# Lab 01: Static Host Inventory

> **Goal:** Ansible can reach every target server using a static INI inventory file you maintain on the control node.
> **Time:** ~45 min · **Difficulty:** Beginner · **Files:** `labs/inventory/hosts.ini.local`

## Overview

Before Ansible can configure anything, it must know **which machines exist** and **how to connect** to them. An inventory file answers both questions. In this lab you create a personal inventory from the repository template, replace placeholder IPs with your AWS private addresses, and prove connectivity with the `ansible.builtin.ping` module.

This is the foundation for every other Ansible lab in the bootcamp. You will reuse `hosts.ini.local` through lab 07.

Static inventory is appropriate when your fleet is small, well-known, and changes infrequently — exactly the pattern used in this curriculum's AWS lab environment.

## Learning objectives

By the end of this lab you will be able to:

- Explain the difference between a control node and managed nodes
- Describe how `ansible.cfg` sets default inventory and connection behavior
- Create and edit a static INI inventory with host groups and connection variables
- Run `ansible` with `-i` to target a group or individual host
- Interpret `SUCCESS`, `UNREACHABLE`, and `FAILED` in ad hoc output
- Use `ansible-inventory` to inspect hosts and merged variables
- Verify SSH connectivity independently of Ansible

## Prerequisites

- [ ] [AWS lab environment](../../../curriculum/setup/aws-lab-environment.md) complete — control node + at least two web targets
- [ ] SSH from control node to each target works: `ssh ubuntu@<private-ip>`
- [ ] Repository cloned at `~/terraform-ansible-labs`
- [ ] Ansible Core 2.14+ installed on the control node

## Exercise index

| Exercise | Topic | Anchor |
|----------|-------|--------|
| [1](#ex1) | Verify Ansible and project layout | Control node setup |
| [2](#ex2) | Create personal inventory from template | `hosts.ini.local` |
| [3](#ex3) | Ping web servers with Ansible | Connectivity test |
| [4](#ex4) | Inventory introspection | `ansible-inventory` |
| [5](#ex5) | Compare repo inventory and `ansible.cfg` | Defaults and conventions |

## What you will build

```
Control node (ansible commands)
        │
        │  SSH :22
        ├──────────► web1  (group: webservers)  10.0.1.10
        └──────────► web2  (group: webservers)  10.0.1.11

Inventory file: inventory/hosts.ini.local
```

No packages are installed on targets in this lab — only connectivity is tested.

---

## Exercise 1 — Verify Ansible on the control node

<a id="ex1"></a>

### Step 1.1 — Check Ansible version

On your **control node** (not your laptop unless it is the control node):

```bash
ansible --version
```

**Validate**

```text
ansible [core 2.14
```

or newer (2.15, 2.16, etc.). The first line must show `ansible [core 2.` with version **2.14 or higher**.

**What happened:** Ansible Core includes the engine, built-in modules, and `ansible-playbook`. The version must be recent enough for FQCN modules (`ansible.builtin.*`) used throughout this bootcamp.

### Step 1.2 — Confirm you are in the labs directory

```bash
cd ~/terraform-ansible-labs/ansible/essentials/labs
pwd
```

**Validate**

```text
/home/ubuntu/terraform-ansible-labs/ansible/essentials/labs
```

(path may vary if your home directory is not `/home/ubuntu`, but must end with `ansible/essentials/labs`).

**What happened:** All essentials playbooks, roles, and inventory templates live under this directory. Staying here avoids path mistakes in later commands.

### Step 1.3 — List inventory template files

```bash
ls -la inventory/
```

**Validate** — you should see at least:

```text
hosts.ini
hosts.ini.local.example
hosts.yaml
group_vars/
```

**What happened:** `hosts.ini` is the committed sample inventory with placeholder IPs. `hosts.ini.local.example` is the template you copy to create your personal inventory. `group_vars/` holds variables that apply to entire groups (used in lab 02).

### Step 1.4 — Review the committed sample inventory

```bash
cat inventory/hosts.ini
```

**Validate** — output matches the repository structure:

```ini
[webservers]
web1 ansible_host=10.0.1.10 ansible_user=ubuntu
web2 ansible_host=10.0.1.11 ansible_user=ubuntu

[webservers:vars]
ansible_python_interpreter=/usr/bin/python3

[dbservers]
db1 ansible_host=10.0.1.20 ansible_user=ubuntu
```

**What happened:** INI inventory uses bracketed **groups** (`[webservers]`), host lines with **connection variables** (`ansible_host`, `ansible_user`), and a `[group:vars]` section for variables that apply to every host in the group. The `dbservers` group is included for later labs even though this exercise focuses on web nodes.

---

## Exercise 2 — Create your personal inventory

<a id="ex2"></a>

### Step 2.1 — Copy the template

```bash
cp inventory/hosts.ini.local.example inventory/hosts.ini.local
```

**Validate**

```bash
ls -la inventory/hosts.ini.local
```

File exists and is readable.

**What happened:** `hosts.ini.local` is git-ignored so your real IPs are never committed. Each learner maintains their own copy while the repository ships safe placeholder addresses.

### Step 2.2 — Open the inventory in an editor

```bash
nano inventory/hosts.ini.local
```

(or `vim` if you prefer)

**Validate** — file contains a section like:

```ini
[webservers]
web1 ansible_host=10.0.1.10 ansible_user=ubuntu
web2 ansible_host=10.0.1.11 ansible_user=ubuntu
```

**What happened:** `[webservers]` defines a **group**. Each line is a **host** with connection variables. `ansible_host` is the IP Ansible uses for SSH; `ansible_user` is the login name. The host name (`web1`) is an inventory alias — it does not have to match the DNS hostname.

### Step 2.3 — Replace placeholder IPs

Edit each `ansible_host=` value to match the **private IP** of your EC2 web nodes from the AWS console or setup guide.

If you have a database node provisioned, update `db1` under `[dbservers]` as well. If not, you may leave `db1` commented out or remove that section for now.

Save and exit (`Ctrl+O`, `Enter`, `Ctrl+X` in nano).

**Validate**

```bash
grep ansible_host inventory/hosts.ini.local
```

Shows your real private IPs (e.g. `10.0.1.45`), not `10.0.1.10` placeholders.

**What happened:** Ansible resolves host names (`web1`, `web2`) to IPs via `ansible_host`. Wrong IPs cause `UNREACHABLE` errors in the next exercise. Private IPs are correct inside a VPC; public IPs are only needed if you SSH from outside the VPC.

### Step 2.4 — Test SSH manually (bypass Ansible)

Pick the first IP from your inventory:

```bash
ssh -o ConnectTimeout=5 ubuntu@<web1-private-ip> "hostname"
```

**Validate**

```text
ip-10-0-1-xx
```

or similar hostname — command exits with code 0.

**What happened:** If manual SSH fails, Ansible will fail too. Fix security groups (port 22 from control node), SSH keys, or IPs before continuing. Ansible does not replace SSH — it orchestrates SSH sessions.

Repeat for `web2` if you have a second node:

```bash
ssh -o ConnectTimeout=5 ubuntu@<web2-private-ip> "hostname"
```

**Validate** — exit code 0 and a hostname printed.

### Step 2.5 — Confirm Python 3 on targets (optional but recommended)

```bash
ssh ubuntu@<web1-private-ip> "python3 --version"
```

**Validate**

```text
Python 3.10.
```

or newer.

**What happened:** Ansible modules execute over SSH using Python on the target. Ubuntu 22.04 ships Python 3. The `[webservers:vars]` section sets `ansible_python_interpreter=/usr/bin/python3` explicitly so Ansible does not guess wrong on minimal images.

---

## Exercise 3 — Ping all web servers with Ansible

<a id="ex3"></a>

### Step 3.1 — Run the ping module against the webservers group

```bash
ansible -i inventory/hosts.ini.local webservers -m ansible.builtin.ping
```

**Validate**

```text
web1 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
web2 | SUCCESS => {
    "changed": false,
    "ping": "pong"
}
```

Both hosts return `"ping": "pong"` and no `FAILED` lines appear.

**What happened:** The `ansible.builtin.ping` module does not use ICMP. It verifies Python on the target and returns `pong` if Ansible can execute a module over SSH. `changed: false` means the module made no configuration change — expected for ping.

### Step 3.2 — Ping a single host by name

```bash
ansible -i inventory/hosts.ini.local web1 -m ansible.builtin.ping
```

**Validate** — only `web1` appears in output with `"ping": "pong"`.

**What happened:** Host patterns can be a group name (`webservers`), a single host (`web1`), or the magic group `all`. Narrow patterns limit blast radius during troubleshooting.

### Step 3.3 — Run ping against all hosts in inventory

```bash
ansible -i inventory/hosts.ini.local all -m ansible.builtin.ping
```

**Validate** — `pong` result for every host in every group (web nodes and db node if present).

**What happened:** `all` is an implicit group containing every host defined in inventory. If `db1` is unreachable because you have not provisioned it, either remove it from inventory or expect one `UNREACHABLE` line — fix before lab 02 if you keep it.

### Step 3.4 — Run ping with verbose output (optional)

```bash
ansible -i inventory/hosts.ini.local webservers -m ansible.builtin.ping -vvv
```

**Validate** — scroll output; you should see SSH connection attempts to your private IPs and the remote Python interpreter path.

**What happened:** `-vvv` is your first troubleshooting tool. It shows which user, which IP, and where SSH or Python fails if something breaks. Increase verbosity only when debugging — normal runs stay quiet.

---

## Exercise 4 — Inventory introspection

<a id="ex4"></a>

### Step 4.1 — List all hosts

```bash
ansible -i inventory/hosts.ini.local all --list-hosts
```

**Validate**

```text
  hosts (2):
    web1
    web2
```

(host count matches your inventory; add `db1` if configured)

**What happened:** Ansible expands groups to host names before running tasks. This command shows the expansion without executing anything on targets.

### Step 4.2 — List hosts in one group only

```bash
ansible -i inventory/hosts.ini.local webservers --list-hosts
```

**Validate**

```text
  hosts (2):
    web1
    web2
```

**What happened:** Group-scoped listing confirms your INI section headers are parsed correctly. Typos in group names (`[webserver]` vs `[webservers]`) cause empty host lists.

### Step 4.3 — Show host variables for one host

```bash
ansible-inventory -i inventory/hosts.ini.local --host web1
```

**Validate** — JSON output includes:

```json
"ansible_host": "10.0.1.xx",
"ansible_user": "ubuntu",
"ansible_python_interpreter": "/usr/bin/python3"
```

(with your real IP)

**What happened:** `ansible-inventory` merges variables from inventory, `group_vars/`, and `host_vars/` (labs 02+). This is essential for debugging variable precedence before you write playbooks.

### Step 4.4 — Show inventory as YAML (optional)

```bash
ansible-inventory -i inventory/hosts.ini.local --list --yaml
```

**Validate** — structured YAML with `all.children.webservers.hosts.web1` keys.

**What happened:** The same logical inventory can be authored as INI or YAML. Lab 02 uses `hosts.yaml`; seeing the parsed structure helps when you switch formats.

---

## Exercise 5 — Compare repo inventory and ansible.cfg

<a id="ex5"></a>

### Step 5.1 — Read ansible.cfg defaults

```bash
cat ansible.cfg
```

**Validate**

```ini
[defaults]
inventory = inventory/hosts.ini
roles_path = roles
host_key_checking = False
interpreter_python = auto_silent
retry_files_enabled = False

[privilege_escalation]
become_method = sudo
```

**What happened:** When you omit `-i`, Ansible loads `inventory/hosts.ini` (placeholder IPs). Labs intentionally pass `-i inventory/hosts.ini.local` so each learner uses their real addresses without editing committed files. `host_key_checking = False` skips SSH host key prompts in lab environments — do not disable this in production without compensating controls.

### Step 5.2 — Observe default inventory behavior

```bash
ansible webservers -m ansible.builtin.ping
```

**Validate** — if you have **not** edited `hosts.ini`, this may try placeholder IPs `10.0.1.10` / `10.0.1.11` and fail with `UNREACHABLE`.

**What happened:** This demonstrates why personal inventory matters. Production teams often use `-i` per environment (`staging.ini`, `prod.ini`) or dynamic inventory plugins instead of editing a single file.

### Step 5.3 — Confirm explicit inventory always works

```bash
ansible -i inventory/hosts.ini.local webservers -m ansible.builtin.ping
```

**Validate** — `pong` on all web hosts.

**What happened:** Explicit `-i inventory/hosts.ini.local` overrides `ansible.cfg` for that invocation. Use this pattern in every lab command until you standardize on a local default.

### Step 5.4 — Syntax-check inventory file (optional)

```bash
ansible-inventory -i inventory/hosts.ini.local --list > /dev/null && echo "Inventory OK"
```

**Validate**

```text
Inventory OK
```

**What happened:** Parsing inventory without connecting to hosts catches INI syntax errors early — mismatched brackets, bad key names, or stray characters.

---

## Key takeaways

- Static inventory is a simple list of hosts and groups — perfect for small, known fleets
- Connection variables (`ansible_host`, `ansible_user`, `ansible_python_interpreter`) belong in inventory or group vars
- Always use `-i inventory/hosts.ini.local` in labs until you configure environment-specific defaults
- `ansible.builtin.ping` tests Ansible connectivity, not network ICMP
- Fix SSH manually before blaming Ansible
- Personal inventory files stay local — never commit real IPs to git
- `ansible-inventory` is the inspector; `ansible` is the executor

## Done when

- [ ] `ansible --version` shows core 2.14+
- [ ] `hosts.ini.local` exists with your real private IPs
- [ ] Manual `ssh ubuntu@<ip>` works for each web node
- [ ] `ansible -i inventory/hosts.ini.local webservers -m ansible.builtin.ping` returns `pong` on every web host
- [ ] `ansible-inventory --host web1` shows correct `ansible_host` and `ansible_user`
- [ ] You understand why `-i inventory/hosts.ini.local` is required in labs

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `UNREACHABLE` | Wrong IP or security group | Verify IP in AWS console; ensure SG allows port 22 from control node |
| `Permission denied (publickey)` | SSH key not on target | `ssh-copy-id -i ~/.ssh/id_rsa.pub ubuntu@<ip>` |
| `Host key verification failed` | Known hosts mismatch | `ssh-keygen -R <ip>` then SSH again |
| `Module not found: ping` | Old Ansible or missing FQCN | Use `ansible.builtin.ping` |
| Only one host works | Typo in second host line | Compare both lines in `hosts.ini.local` |
| `sudo: a password is required` | Not expected in this lab | Ping does not need `-b`; ignore unless you added `-b` |
| Empty host list | Wrong group name in command | Match `[webservers]` exactly in inventory |
| Works with `-i` but not without | `ansible.cfg` points at `hosts.ini` | Always pass `-i inventory/hosts.ini.local` in labs |

## Cleanup

No cloud resources to destroy. Keep `inventory/hosts.ini.local` — every subsequent lab builds on it.

```bash
# Optional: verify inventory is still valid
ansible -i inventory/hosts.ini.local webservers -m ansible.builtin.ping
```

## Reference links

- [Inventory deep dive](../docs/02-inventory/inventory-ini-and-yaml.md)
- [Interactive inventory flow](../html/inventory-flow.html)
- [Ansible inventory documentation](https://docs.ansible.com/ansible/latest/inventory_guide/intro_inventory.html)
- [Connection variables](https://docs.ansible.com/ansible/latest/inventory_guide/intro_inventory.html#connecting-to-hosts-behavioral-inventory-parameters)

## Next steps

- [Lab 02 — Hosts, groups, and group variables](lab02-inventory-hosts-groups.md)
- [Lab manual index](README.md)
- [Interactive catalog](../html/index.html)

---
*Source: Ansible Essentials bootcamp · Lesson 2 · Next: [lab02](lab02-inventory-hosts-groups.md)*
