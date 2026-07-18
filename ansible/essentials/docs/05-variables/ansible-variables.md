# Ansible Variables and Templates

## Objective (conceptual)

**Variables** parameterize playbooks—ports, package names, environment labels—without duplicating YAML. They arrive from inventory, `group_vars/`, play `vars:`, role `defaults/`, registered task output, and **facts**. **Templates** (Jinja2 `.j2` files) render variables into config files on managed nodes.

The mental model: variables are **inputs**; facts are **discovered inputs**; templates are **mail merge** for `/etc/` files.

**Interactive reference:** [Variables and Templates](../../html/variables-templates.html)

## Variable precedence (simplified)

Higher wins when the same name is defined in multiple places:

1. Extra vars (`-e` on CLI)
2. Task vars / `include_vars`
3. Block / play `vars:`
4. Role vars and `include_params`
5. `group_vars` / `host_vars`
6. Role `defaults/`
7. Facts

## group_vars example

`inventory/group_vars/webservers.yml`:

```yaml
---
webserver_port: 80
app_env: production
```

Referenced in templates and tasks as `{{ webserver_port }}`.

## Template task (Lab 05)

```yaml
---
- name: Deploy MOTD from template
  hosts: webservers
  become: true
  tasks:
    - name: Template motd
      ansible.builtin.template:
        src: ../templates/motd.j2
        dest: /etc/motd
        mode: "0644"
```

`templates/motd.j2`:

```jinja2
Welcome to {{ inventory_hostname }}
Environment: {{ app_env }}
Web port: {{ webserver_port }}
```

- `inventory_hostname` — built-in fact (inventory name).
- `app_env`, `webserver_port` — from `group_vars`.

## Jinja2 essentials

| Expression | Example |
|------------|---------|
| Variable | `{{ ansible_facts.distribution }}` |
| Filter | `{{ name \| upper }}` |
| Default | `{{ port \| default(80) }}` |
| Conditional inline | `{% if app_env == 'production' %}...{% endif %}` |

Keep complex logic in vars files or roles—not deeply nested templates.

## Registering task output

```yaml
- name: Check apache status
  ansible.builtin.command: systemctl is-active apache2
  register: apache_status
  changed_when: false
  failed_when: false

- name: Show status
  ansible.builtin.debug:
    msg: "Apache is {{ apache_status.stdout }}"
```

`register` creates a variable (`apache_status`) for later tasks.

## Facts vs variables

- **Facts** — discovered via `setup` (OS, IPs, mounts).
- **Variables** — you define in inventory or playbooks.
- Prefix facts with `ansible_facts.` in modern Ansible (`ansible_facts.os_family`).

## Vault variables (preview)

Encrypted secrets live in vault files; decrypted at runtime with `--vault-password-file` (vault chapter).

## vars_prompt (interactive)

Rare in CI but useful in workshops:

```yaml
vars_prompt:
  - name: app_env
    prompt: "Environment name"
    private: false
```

Prefer `group_vars` and `-e` for repeatable automation.

## Operational commands (reference)

```bash
cd ansible/essentials/labs
ansible-playbook playbooks/vars-demo.yml --check --diff
ansible webservers -m ansible.builtin.debug -a "var=hostvars[inventory_hostname]"
ansible-playbook playbooks/vars-demo.yml -e "app_env=staging"
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 05: Playbook Variables](../../labmanuals/lab05-playbook-variables.md) | group_vars, templates, Jinja2 |
| [Extended: Variables and Templates](../../../extended/docs/playbooks/variables-and-templates.md) | Lookups, extended patterns |
