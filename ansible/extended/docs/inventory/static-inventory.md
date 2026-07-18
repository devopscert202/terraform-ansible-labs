# Static Inventory Patterns (Extended)

## Objective (conceptual)

**Static inventory** lists hosts in files you edit directly—INI or YAML—ideal for labs, small fleets, and brownfield servers with stable IPs. Extended labs add **multiple tiers** (`webservers`, `appservers`) and group-level connection variables so one playbook can target different layers.

The mental model: static inventory is a **spreadsheet exported to text**—simple, explicit, and perfect until cloud autoscaling makes host lists change hourly.

**Interactive reference:** [Dynamic Inventory](../../html/dynamic-inventory.html) (contrast with static)

## Extended INI inventory

`inventory/hosts.ini`:

```ini
# Replace private IPs with your lab environment (Ubuntu 22.04)
[webservers]
web1 ansible_host=10.0.1.10
web2 ansible_host=10.0.1.11

[appservers]
app1 ansible_host=10.0.1.12

[webservers:vars]
ansible_user=ubuntu
ansible_python_interpreter=/usr/bin/python3

[appservers:vars]
ansible_user=ubuntu
ansible_python_interpreter=/usr/bin/python3
```

- Tier separation maps to architecture (web front, app back).
- `:vars` stanzas DRY connection settings per group.

## group_vars layering

`group_vars/all.yml`:

```yaml
---
lab_environment: extended
nodejs_version: "20"
nodejs_app_port: 3000
nodejs_app_name: lab-app
```

`all` group applies variables to every host; tier-specific overrides go in `group_vars/webservers.yml` or play `vars:`.

## Host patterns across tiers

```yaml
- name: Configure web tier with roles
  hosts: webservers
  become: true
  roles:
    - role: common
    - role: webserver

- name: Configure app tier with roles
  hosts: appservers
  become: true
  roles:
    - role: common
    - role: nodejs_app
```

Each play runs only on its pattern—no accidental Node.js install on webservers.

## Inventory verification

```bash
ansible-inventory -i inventory/hosts.ini --graph
ansible-inventory -i inventory/hosts.ini --host web1
ansible appservers --list-hosts
```

## When static inventory breaks down

- Autoscaling groups add/remove instances hourly.
- Ephemeral containers with new IPs every deploy.
- Multi-region fleets with hundreds of hosts.

→ Use dynamic inventory plugins (AWS EC2 chapter).

## Static inventory hygiene

- Keep **connection vars** in inventory; secrets in Vault.
- Document replacement placeholders (`10.0.1.10`) in comments.
- Commit example inventory; gitignore `*.local` overrides with real IPs if needed.

## Merging inventories (concept)

Ansible can combine multiple `-i` sources:

```bash
ansible-playbook site.yml -i inventory/hosts.ini -i inventory/aws_ec2.yml
```

Use carefully—duplicate hostnames collide. Extended labs keep static and dynamic exercises separate until you understand each.

## Children and parent groups

YAML inventory can nest `children` under `all` for composite groups (`production: children: [webservers, dbservers]`). INI uses `:children` suffix headers—see essentials Lab 02 for both styles.

## Operational commands (reference)

```bash
cd ansible/extended/labs
ansible -i inventory/hosts.ini all -m ansible.builtin.ping
ansible-playbook playbooks/site.yml -i inventory/hosts.ini --limit webservers
ansible-inventory -i inventory/hosts.ini --vars --host web1
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Essentials Lab 02: Hosts and Groups](../../../essentials/labmanuals/lab02-inventory-hosts-groups.md) | INI and YAML static inventory fundamentals |
| [Extended Lab 08: Roles Project](../../labmanuals/lab08-roles-project.md) | Multi-tier static inventory with site playbook |
