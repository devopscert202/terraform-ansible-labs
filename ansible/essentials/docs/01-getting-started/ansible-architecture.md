# Ansible Architecture

## Objective (conceptual)

Ansible automates configuration through **SSH (or WinRM)** from a **control node**—your laptop or a CI runner—without installing an agent on managed hosts. You declare **desired state** in YAML playbooks; Ansible compares that to reality and runs **tasks** using **modules** (small programs invoked over the connection).

The mental model: Terraform provisions infrastructure; Ansible **configures** what already exists. Inventory answers *where*; playbooks answer *what*; modules answer *how*.

**Interactive reference:** [Ansible Architecture](../../html/ansible-architecture.html)

## Core components

| Component | Role |
|-----------|------|
| **Control node** | Runs `ansible` / `ansible-playbook`; holds playbooks and inventory |
| **Managed node** | Target host reached over SSH |
| **Inventory** | List of hosts and groups (`webservers`, `dbservers`) |
| **Playbook** | Ordered list of plays, each targeting a host pattern |
| **Task** | One module invocation with parameters |
| **Module** | Idempotent unit of work (`ansible.builtin.apt`, `ansible.builtin.service`) |
| **Facts** | Variables Ansible discovers about a host (hostname, OS, IP) |
| **Handlers** | Tasks that run only when notified (often service restarts) |

## Execution flow

```
ansible-playbook site.yml
    → read inventory + ansible.cfg
    → connect to each host in parallel (forks)
    → gather facts (unless disabled)
    → run tasks in order; notify handlers at end of play
```

No central database—state is whatever exists on the targets after each run.

## ansible.cfg (essentials labs)

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

- `inventory` — default host list for all commands.
- `roles_path` — where role directories are discovered.
- `become_method = sudo` — privilege escalation for package installs.

## FQCN modules

Use fully qualified collection names for clarity and exam alignment:

```yaml
- name: Install apache2
  ansible.builtin.apt:
    name: apache2
    state: present
    update_cache: true
```

`apt` alone still resolves on many systems; `ansible.builtin.apt` is explicit.

## Push vs pull

Ansible is **push-based**: the control node initiates change. (Ansible-pull exists but is uncommon in introductory labs.)

## Relationship to inventory and playbooks

- **Inventory** defines `web1`, `web2` under `webservers`.
- **Playbook** selects `hosts: webservers` and applies tasks.
- **Variables** layer from `group_vars/`, play `vars:`, and facts.

## Security posture (labs)

- SSH keys or `ansible_user` per host—no passwords in playbooks.
- `become: true` only when tasks need root (packages, services).
- Vault encrypts secrets at rest (covered in vault chapter).

## Parallelism and forks

Ansible connects to many hosts in parallel (`forks=5` default in `ansible.cfg`). Large change windows may lower forks to avoid overwhelming network or package mirrors.

```bash
ansible webservers -m ansible.builtin.ping -f 1   # serial ping
```

## Collections and ansible.builtin

Modules ship in **collections**. The `ansible.builtin` collection is bundled with Ansible 2.10+; FQCN makes playbooks explicit and matches RHCE-style exams.

```bash
ansible-doc ansible.builtin.apt
ansible-galaxy collection list ansible.builtin
```

## Control node requirements

The machine running Ansible needs:

- Python 3 on control node
- SSH client and key-based access to targets
- Same major Ansible version documented in lab manuals

Managed nodes need Python for most modules (installed by default on Ubuntu cloud images).

## Operational commands (reference)

```bash
cd ansible/essentials/labs
ansible --version
ansible webservers -m ansible.builtin.ping
ansible-inventory --list
ansible-playbook playbooks/apache.yml --check
ansible-config dump | grep DEFAULTS
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 01: Static Inventory](../../labmanuals/lab01-inventory-static-hosts.md) | Hosts, groups, `ansible.cfg`, connectivity |
| [Lab 02: Inventory Hosts and Groups](../../labmanuals/lab02-inventory-hosts-groups.md) | Group vars, patterns, limits |
