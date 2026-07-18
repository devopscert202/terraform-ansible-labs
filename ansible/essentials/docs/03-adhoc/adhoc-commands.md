# Ansible Ad Hoc Commands

## Objective (conceptual)

**Ad hoc** commands run a single module against a host pattern without a playbook file. They are ideal for quick checks (`ping`), one-off facts (`setup`), or emergencies—but repeated work belongs in playbooks under version control.

The mental model: ad hoc is the **sticky note**; playbooks are the **runbook**. Use ad hoc to explore; promote stable operations to YAML.

**Interactive reference:** [Ad Hoc vs Playbook](../../html/adhoc-vs-playbook.html)

## Command shape

```bash
ansible <pattern> -m <module> -a "<module args>" [options]
```

Common options:

- `-i inventory/hosts.ini` — inventory path (default from `ansible.cfg`)
- `-b` / `--become` — privilege escalation (sudo)
- `-m` — module name (FQCN recommended)
- `-a` — module arguments as a string
- `--check` — dry run where supported

## Connectivity check

```bash
ansible webservers -m ansible.builtin.ping
```

Success returns `pong`—SSH and Python interpreter work.

## Package inspection (become required)

```bash
ansible webservers -b -m ansible.builtin.apt -a "name=apache2 state=present"
```

Prefer playbooks for installs so change is reviewed in git.

## Facts snapshot

```bash
ansible webservers -m ansible.builtin.setup -a "filter=ansible_os_family,ansible_distribution*"
```

`setup` is the facts module; filters limit output size.

## Command vs shell

| Module | Use |
|--------|-----|
| `ansible.builtin.command` | Run command, no shell features; safer default |
| `ansible.builtin.shell` | Pipes, redirects, `$(...)` — use sparingly |

```bash
ansible webservers -m ansible.builtin.command -a "uptime"
```

Avoid `shell` when `command` or a dedicated module suffices.

## Copy and file operations

```bash
ansible webservers -b -m ansible.builtin.copy -a "src=./motd.txt dest=/etc/motd mode=0644"
```

For templates with variables, use `ansible.builtin.template` in a playbook instead.

## Limits and serial

```bash
ansible webservers -m ansible.builtin.ping --limit web1
```

`--limit` restricts blast radius during maintenance.

## When to switch to playbooks

- More than one related task
- Handlers needed (service restart after config change)
- Roles, variables, or Vault secrets involved
- CI/CD pipeline execution

## Verbose troubleshooting

```bash
ansible webservers -m ansible.builtin.ping -vvv
```

`-v` through `-vvvv` increases connection and module verbosity—start at `-vvv` for SSH failures.

## Raw module output

```bash
ansible webservers -m ansible.builtin.apt -a "name=apache2 state=present" -b -o
```

`-o` summarizes output on one line per host—easier to scan in large inventories.

## Dry run limitations

`--check` mode is not supported by every module (`command`, `shell`, some cloud APIs). Read module documentation before relying on check mode for production change windows.

## Operational commands (reference)

```bash
cd ansible/essentials/labs
ansible --version
ansible-doc ansible.builtin.apt
ansible webservers -m ansible.builtin.ping
ansible all -m ansible.builtin.setup --tree /tmp/facts
ansible-playbook playbooks/apache.yml   # promoted pattern
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 03: Ad Hoc Commands](../../labmanuals/lab03-adhoc-commands.md) | ping, command, apt, setup, limits |
| [Extended Lab 01: Ad Hoc Modules](../../../extended/labmanuals/lab01-adhoc-modules.md) | Deeper module exploration and documentation |
