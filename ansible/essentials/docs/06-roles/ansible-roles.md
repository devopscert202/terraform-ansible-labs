# Ansible Roles

## Objective (conceptual)

A **role** is a portable directory layout for tasks, handlers, defaults, vars, templates, and files. Instead of one long playbook, you call `roles: - webserver` and Ansible loads conventional paths automatically. Roles enable reuse across playbooks and sharing via Ansible Galaxy or internal git repos.

The mental model: a role is a **mini-package** with an API (`defaults` and `vars` in, service status out).

**Interactive reference:** [Roles and Vault](../../html/roles-and-vault.html)

## Standard role layout

```
roles/webserver/
├── defaults/main.yml    # lowest precedence variables
├── tasks/main.yml       # entry task list
├── handlers/main.yml    # handler definitions
├── templates/           # Jinja2 templates
├── files/               # static files
└── meta/main.yml        # role metadata and dependencies
```

## Playbook invoking a role

```yaml
---
- name: Site with webserver role
  hosts: webservers
  become: true
  roles:
    - webserver
```

`roles_path = roles` in `ansible.cfg` resolves the directory name.

## Role tasks excerpt

`roles/webserver/tasks/main.yml`:

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

Variables `web_package` and `web_service` typically come from `defaults/main.yml` so consumers can override without editing tasks.

## Role parameters

Pass overrides inline:

```yaml
roles:
  - role: webserver
    vars:
      web_package: nginx
```

Or use `group_vars` / `host_vars` for environment-specific values.

## Handlers in roles

Define handlers in `handlers/main.yml`; tasks `notify` by **name** string. Handlers flush at end of play unless `ansible.builtin.meta: flush_handlers` runs earlier.

## Multiple roles in site playbooks

Extended `site.yml` pattern:

```yaml
---
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

`common` role applies baseline packages; tier roles add specialization.

## When to extract a role

- Same tasks appear in two playbooks.
- You want versioned releases (`meta/main.yml` dependencies).
- Team boundaries: platform owns `common`, app team owns `nodejs_app`.

## Role vs playbook

| Playbook | Role |
|----------|------|
| Top-level entry, selects hosts | No `hosts:` — caller provides |
| May list multiple roles | Single focused purpose |
| Run with `ansible-playbook` | Invoked via `roles:` list |

## Operational commands (reference)

```bash
cd ansible/essentials/labs
ansible-galaxy role init myrole    # scaffold new role
ansible-playbook playbooks/role-site.yml
ansible-playbook playbooks/role-site.yml --tags install   # if tags defined
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 06: Create Roles](../../labmanuals/lab06-roles-create.md) | Build `webserver` role from playbook tasks |
| [Extended Lab 08: Roles Project](../../../extended/labmanuals/lab08-roles-project.md) | Multi-role site playbook |
