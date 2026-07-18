# Extended Playbook Structure

## Objective (conceptual)

Production playbooks split work by **tier** (web, app), **role**, and **concern** (install vs deploy). A **site playbook** orchestrates multiple plays in one file—or imports smaller playbooks—so CI runs one entry point. Extended labs structure Node.js deployment as many small, named tasks with registers, handlers, and templates.

The mental model: essentials playbooks are **one room renovation**; extended playbooks are **whole-site construction** with electricians and plumbers scheduled in sequence.

**Interactive reference:** [Loops and Conditionals](../../html/loops-conditionals.html)

## Site playbook layout

```yaml
---
# Site playbook — applies roles (Lesson 6 LEP)
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

Each play has its own `hosts`, `become`, and `roles` list—failures isolate to a tier.

## Node.js playbook excerpt (multi-task)

From `playbooks/nodejs.yml`:

```yaml
---
- name: Install Node.js and deploy lab application
  hosts: appservers
  become: true
  tasks:
    - name: Install prerequisite packages
      ansible.builtin.apt:
        name:
          - ca-certificates
          - curl
          - gnupg
        state: present
        update_cache: true

    - name: Verify Node.js version
      ansible.builtin.command: node --version
      register: node_version
      changed_when: false

    - name: Display Node.js version
      ansible.builtin.debug:
        msg: "Node.js installed: {{ node_version.stdout }}"
```

- `register` captures output for later tasks.
- `changed_when: false` on read-only commands keeps reports accurate.

## Shared variables

`group_vars/all.yml` supplies app-wide defaults:

```yaml
---
lab_environment: extended
nodejs_version: "20"
nodejs_app_port: 3000
nodejs_app_name: lab-app
```

Playbooks reference `{{ nodejs_version }}` in repository URLs and paths.

## Handlers block at play bottom

```yaml
  handlers:
    - name: Reload systemd
      ansible.builtin.systemd:
        daemon_reload: true

    - name: Restart nodejs app
      ansible.builtin.systemd:
        name: "{{ nodejs_app_name }}"
        state: restarted
```

Template tasks `notify` these handlers when app or unit files change.

## Playbook organization options

| Pattern | When |
|---------|------|
| Single `site.yml` | Small projects, labs |
| `import_playbook` | Reuse plays across environments |
| Role-only plays | Logic lives in roles; playbook is thin |
| Tags | `--tags deploy` for partial runs |

## Validation before apply

```bash
ansible-playbook playbooks/nodejs.yml --syntax-check
ansible-playbook playbooks/site.yml --list-tasks
ansible-playbook playbooks/site.yml --check
```

## Operational commands (reference)

```bash
cd ansible/extended/labs
ansible-playbook playbooks/site.yml --list-hosts
ansible-playbook playbooks/nodejs.yml --step
ansible-playbook playbooks/site.yml --limit appservers
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 03: Node.js Playbook](../../labmanuals/lab03-nodejs-playbook.md) | Multi-stage app install and systemd deploy |
| [Lab 08: Roles Project](../../labmanuals/lab08-roles-project.md) | Site playbook with common, webserver, nodejs_app roles |
