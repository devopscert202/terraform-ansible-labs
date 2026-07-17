# Ansible Architecture

> **Curriculum:** Ansible Essentials · **Brand:** `#EE0000` · **Lab targets:** Ubuntu 22.04 · **SSH:** port 22

## Overview

Ansible is an agentless automation engine that connects to remote hosts over SSH, pushes small Python modules, executes them, and collects results. In this curriculum, **Terraform provisions** the AWS lab infrastructure (VPC, subnets, EC2 instances), and **Ansible configures** those instances after they are reachable.

The control node (your laptop or a CI runner) holds playbooks, inventory, roles, and vault files under `ansible/essentials/labs/`. Managed nodes (`web1`, `web2`, `db1`) require no permanent Ansible agent—only SSH access and Python 3.

Understanding Ansible's architecture helps you debug connectivity issues, interpret playbook output, and design reusable automation that scales from ad hoc commands to role-based site playbooks.

**Interactive reference:** [ansible-architecture.html](../../html/ansible-architecture.html)

---

## Key Concepts

| Component | Purpose | Location in this repo |
|-----------|---------|----------------------|
| **Control node** | Runs `ansible` and `ansible-playbook` CLI | Your workstation |
| **Managed node** | Target host receiving configuration | `web1`, `web2`, `db1` (Ubuntu 22.04) |
| **Inventory** | Defines hosts, groups, and connection vars | `labs/inventory/hosts.ini` |
| **Playbook** | Declarative YAML automation document | `labs/playbooks/*.yml` |
| **Module** | Unit of work (install package, copy file) | FQCN e.g. `ansible.builtin.apt` |
| **Plugin** | Extends connection, inventory, callbacks | Built into Ansible core |
| **Role** | Reusable bundle of tasks, defaults, handlers | `labs/roles/webserver/` |
| **ansible.cfg** | Project-level defaults | `labs/ansible.cfg` |

### Connection and Execution Model

| Stage | What happens | Typical duration |
|-------|--------------|------------------|
| 1. Parse | Load `ansible.cfg`, inventory, playbook | Milliseconds |
| 2. Connect | SSH to `ansible_host` on port 22 | 1–3 seconds |
| 3. Transfer | Push module + arguments over SSH | Sub-second |
| 4. Execute | Run module with Python on target | Varies by task |
| 5. Report | Return JSON result to control node | Sub-second |

### Inventory Groups in the Lab

| Group | Hosts | IP (lab default) | Role |
|-------|-------|------------------|------|
| `webservers` | `web1`, `web2` | `10.0.1.10`, `10.0.1.11` | Apache / Node.js |
| `dbservers` | `db1` | `10.0.1.20` | Database tier |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CONTROL NODE (you)                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ ansible.cfg  │  │  inventory/  │  │  playbooks/  │  │   roles/    │  │
│  │              │  │  hosts.ini   │  │  apache.yml  │  │  webserver/ │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬──────┘  │
│         │                 │                 │                 │         │
│         └─────────────────┴────────┬────────┴─────────────────┘         │
│                                    │                                    │
│                          ansible-playbook                               │
│                                    │                                    │
└────────────────────────────────────┼────────────────────────────────────┘
                                     │ SSH :22
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
              ▼                      ▼                      ▼
     ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
     │  web1           │   │  web2           │   │  db1            │
     │  10.0.1.10      │   │  10.0.1.11      │   │  10.0.1.20      │
     │  Ubuntu 22.04   │   │  Ubuntu 22.04   │   │  Ubuntu 22.04   │
     │  python3        │   │  python3        │   │  python3        │
     └─────────────────┘   └─────────────────┘   └─────────────────┘
              ▲                      ▲                      ▲
              │                      │                      │
              └──────────────────────┴──────────────────────┘
                          Provisioned by Terraform (AWS)
```

### Data Flow for a Single Task

```
Playbook task          Module arguments           Target host
─────────────          ────────────────           ───────────
ansible.builtin.apt  →  { name: apache2,     →   apt installs
                        state: present }         apache2 package
                              │
                              ▼
                     JSON result { changed: true,
                                 msg: "ok" }
                              │
                              ▼
                     Printed in playbook recap
```

---

## Project Layout

```
ansible/essentials/
├── docs/                    ← You are here (concept documentation)
├── html/                    ← Interactive diagrams
├── labmanuals/              ← Step-by-step lab exercises
└── labs/                    ← Runnable Ansible project
    ├── ansible.cfg
    ├── inventory/
    │   ├── hosts.ini
    │   ├── hosts.yaml
    │   └── group_vars/webservers.yml
    ├── playbooks/
    ├── roles/webserver/
    ├── templates/motd.j2
    └── vault/secrets.yml
```

---

## Configuration: ansible.cfg

The lab project pins critical defaults in `labs/ansible.cfg`:

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

| Setting | Effect |
|---------|--------|
| `inventory` | Default inventory file; no `-i` flag required |
| `roles_path` | Ansible finds `webserver` role under `labs/roles/` |
| `host_key_checking = False` | Skips SSH host key prompt (lab only; use known_hosts in production) |
| `become_method = sudo` | Privilege escalation via `sudo` when `become: true` |

Always run Ansible commands from `ansible/essentials/labs/` so `ansible.cfg` is discovered automatically.

---

## FQCN Module Examples

Ansible recommends **Fully Qualified Collection Names (FQCN)** for clarity and forward compatibility.

### Connectivity Check

```bash
cd ansible/essentials/labs
ansible webservers -m ansible.builtin.ping
```

Expected output:

```
web1 | SUCCESS => { "ping": "pong" }
web2 | SUCCESS => { "ping": "pong" }
```

### Gather Facts

```bash
ansible web1 -m ansible.builtin.setup -a "filter=ansible_distribution*"
```

### Run a Command (Ad Hoc)

```bash
ansible dbservers -m ansible.builtin.command -a "hostname" -b
```

The `-b` flag enables `become` (sudo) per `ansible.cfg` privilege escalation settings.

### Install a Package via Playbook

From `labs/playbooks/apache.yml`:

```yaml
- name: Install apache2
  ansible.builtin.apt:
    name: apache2
    state: present
    update_cache: true
```

---

## Terraform + Ansible Workflow

```
┌──────────────┐     terraform apply      ┌──────────────┐
│  Terraform   │ ───────────────────────► │  AWS EC2     │
│  (provision) │                          │  instances   │
└──────────────┘                          └──────┬───────┘
                                                 │
                                    SSH reachable on :22
                                                 │
┌──────────────┐     ansible-playbook           │
│  Ansible     │ ◄──────────────────────────────┘
│  (configure) │
└──────────────┘
```

1. **Terraform** creates VPC, security groups, and EC2 instances.
2. Update `inventory/hosts.ini` with actual private IPs (or use a dynamic inventory plugin in advanced scenarios).
3. **Ansible** installs packages, templates files, and enforces desired state.

Separation of concerns: Terraform owns *infrastructure lifecycle*; Ansible owns *configuration drift correction*.

---

## Idempotency and Declarative State

Ansible modules are designed to be **idempotent**—running the same task twice should not cause unnecessary changes.

| First run | Second run |
|-----------|------------|
| `changed=1` (package installed) | `changed=0` (already present) |
| Service started | Service already running |

The recap line `PLAY RECAP` shows per-host `ok`, `changed`, `failed`, and `unreachable` counts.

---

## Version and Environment Requirements

| Requirement | Lab value |
|-------------|-----------|
| Ansible | 2.14+ (ansible-core) |
| Python on control node | 3.9+ |
| Python on targets | 3.x (`/usr/bin/python3`) |
| OS on targets | Ubuntu 22.04 LTS |
| SSH port | 22 |
| User | `ubuntu` (default AWS AMI user) |

Verify Ansible installation:

```bash
ansible --version
```

---

## Troubleshooting

| Symptom | Likely cause | Resolution |
|---------|--------------|------------|
| `UNREACHABLE!` for all hosts | Wrong IP, security group blocks SSH, instance stopped | Verify Terraform outputs; check SG allows TCP 22 from your IP |
| `Permission denied (publickey)` | SSH key not loaded or wrong user | `ssh -i key.pem ubuntu@10.0.1.10`; match `ansible_user` in inventory |
| `ansible.cfg` not applied | Running from wrong directory | `cd ansible/essentials/labs` before commands |
| `python: not found` on target | Python missing or wrong interpreter | Set `ansible_python_interpreter=/usr/bin/python3` in inventory |
| `Host key verification failed` | `host_key_checking` not disabled and new host | Use lab `ansible.cfg` or add host to `known_hosts` |
| Slow first connection | SSH multiplexing cold start | Normal; subsequent tasks reuse connection |
| `sudo: a password is required` | `become` without NOPASSWD sudo | Configure sudoers on target or pass `--ask-become-pass` |
| Module not found | Missing collection | `ansible-galaxy collection install namespace.name` |

### Diagnostic Commands

```bash
# Verbose SSH debugging
ansible web1 -m ansible.builtin.ping -vvv

# Test raw SSH outside Ansible
ssh -i ~/.ssh/lab-key.pem -p 22 ubuntu@10.0.1.10

# List inventory as Ansible sees it
ansible-inventory --list
```

---

## Hands-on Labs

| Lab | Topic | Manual |
|-----|-------|--------|
| — | Prerequisites | [AWS lab environment](../../../../curriculum/setup/aws-lab-environment.md) |
| Lab 01 | Static inventory | [lab01-inventory-static-hosts.md](../../labmanuals/lab01-inventory-static-hosts.md) |
| Lab 02 | Hosts and groups | [lab02-inventory-hosts-groups.md](../../labmanuals/lab02-inventory-hosts-groups.md) |
| Lab 03 | Ad hoc commands | [lab03-adhoc-commands.md](../../labmanuals/lab03-adhoc-commands.md) |

**HTML companion:** [ansible-architecture.html](../../html/ansible-architecture.html)

---

## Security Notes for Production

| Lab setting | Production recommendation |
|-------------|--------------------------|
| `host_key_checking = False` | Enable host key checking; maintain `known_hosts` |
| Plaintext vault secrets | Encrypt with `ansible-vault`; store password in secrets manager |
| Static private IPs | Use dynamic inventory (AWS EC2 plugin, etc.) |
| Shared `ubuntu` user | Dedicated service accounts with least privilege |

---

## Next Steps

1. Read [Configuration Management and IaC](configuration-management-and-iac.md) for the broader automation landscape.
2. Study [Inventory: INI and YAML](../02-inventory/inventory-ini-and-yaml.md) to understand how `hosts.ini` maps to your Terraform outputs.
3. Complete Lab 01 and Lab 02 to validate connectivity to all three hosts.
4. Explore the interactive [inventory flow diagram](../../html/inventory-flow.html).

---

## Quick Reference Card

```bash
# From labs directory
cd ansible/essentials/labs

# Ping all web servers
ansible webservers -m ansible.builtin.ping

# Run Apache playbook
ansible-playbook playbooks/apache.yml

# Check syntax without executing
ansible-playbook playbooks/apache.yml --syntax-check

# Dry run (no changes)
ansible-playbook playbooks/apache.yml --check
```

| Command | Purpose |
|---------|---------|
| `ansible` | Ad hoc module execution |
| `ansible-playbook` | Run YAML playbooks |
| `ansible-inventory` | Inspect parsed inventory |
| `ansible-config dump` | Show effective configuration |
