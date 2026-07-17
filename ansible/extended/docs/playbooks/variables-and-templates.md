# Variables and Templates

Variables parameterize playbooks; Jinja2 templates generate configuration files from variables and facts. Together they separate **data** from **structure** — change a port in `group_vars` without editing task logic. Labs 03, 06, and 08 rely heavily on templates in `playbooks/templates/` and `roles/*/templates/`.

## Learning objectives

- Understand Ansible variable precedence
- Use Jinja2 syntax in templates and task arguments
- Register command output for later tasks
- Apply defaults and filters safely
- Organize variables across inventory, play, and role layers

## Variable sources and precedence

When the same variable name appears in multiple places, Ansible resolves using precedence (highest wins):

| Priority (high → low) | Source | Example |
|----------------------|--------|---------|
| 1 | Extra vars (`-e`) | `-e nodejs_app_port=3001` |
| 2 | Task vars | `vars:` on individual task |
| 3 | Block vars | `vars:` on block |
| 4 | Role and include params | `roles: [{role: x, vars: {...}}]` |
| 5 | `set_fact` / registered vars | Runtime facts |
| 6 | Host facts / `ansible_local` | setup module |
| 7 | `host_vars` | `host_vars/web1.yml` |
| 8 | `group_vars` | `group_vars/all.yml` |
| 9 | Inventory `host_vars` / `group_vars` | INI `[group:vars]` |
| 10 | Role `vars/main.yml` | Role internal vars |
| 11 | Role `defaults/main.yml` | Lowest — designed for overrides |

### Practical example from extended labs

```yaml
# roles/nodejs_app/defaults/main.yml
nodejs_app_port: 3000

# group_vars/all.yml
nodejs_app_port: 3000
nodejs_version: "20"

# Command line override (wins)
ansible-playbook site.yml -e "nodejs_app_port=3001"
```

## Defining variables

### Play vars

```yaml
- hosts: appservers
  vars:
    nodejs_version: "20"
    nodejs_app_name: lab-app
```

### group_vars/all.yml

```yaml
---
nodejs_version: "20"
nodejs_app_port: 3000
nodejs_app_name: lab-app
```

### Role defaults

```yaml
# roles/webserver/defaults/main.yml
webserver_port: 80
webserver_server_name: "{{ inventory_hostname }}"
```

Defaults are intentionally overridable — put common values here.

### Extra vars

```bash
ansible-playbook playbooks/nodejs.yml -e "nodejs_app_port=3001"
ansible-playbook playbooks/conditionals-os.yml -e "enable_firewall=true"
```

Extra vars cannot be overridden by anything except themselves.

## Referencing variables

### In tasks

```yaml
- ansible.builtin.debug:
    msg: "App {{ nodejs_app_name }} on port {{ nodejs_app_port }}"
```

### In module parameters

```yaml
- ansible.builtin.apt:
    name: "{{ package_name }}"
    state: present
```

### Mandatory quoting

When value starts with `{{`, quote the entire expression:

```yaml
name: "{{ item }}"          # Correct
dest: "/opt/{{ app_name }}" # Correct
```

## Jinja2 in templates

Templates use `.j2` extension in `templates/` directory.

### nginx-lab.conf.j2

```jinja2
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name {{ inventory_hostname }};
    root /var/www/html;
    index index.html;
}
```

### app.js.j2 (Node.js lab)

```jinja2
const http = require('http');
const port = {{ nodejs_app_port }};

const server = http.createServer((req, res) => {
  res.writeHead(200, {'Content-Type': 'text/plain'});
  res.end('Hello from {{ nodejs_app_name }} on {{ inventory_hostname }}\n');
});

server.listen(port, '127.0.0.1');
```

### index.html.j2 (webserver role)

```jinja2
<!DOCTYPE html>
<html>
<head><title>{{ inventory_hostname }}</title></head>
<body>
  <h1>Configured by Ansible role: webserver</h1>
  <p>Host: {{ inventory_hostname }}</p>
  <p>Port: {{ webserver_port }}</p>
</body>
</html>
```

### Template task

```yaml
- ansible.builtin.template:
    src: app.js.j2
    dest: "/opt/{{ nodejs_app_name }}/app.js"
    mode: "0644"
    owner: ubuntu
    group: ubuntu
  notify: Restart lab-app
```

`src` is relative to `templates/` in playbook or role.

## Jinja2 filters

| Filter | Example | Result |
|--------|---------|--------|
| `default` | `{{ var \| default('none') }}` | Fallback value |
| `bool` | `{{ enable_firewall \| bool }}` | Boolean coercion |
| `length` | `{{ packages \| length }}` | List size |
| `upper` | `{{ name \| upper }}` | Uppercase |
| `join` | `{{ list \| join(',') }}` | Join list |
| `dict2items` | `{{ mydict \| dict2items }}` | Dict to loopable list |

### Safe defaults in conditionals

```yaml
when: enable_feature | default(false) | bool
```

## Built-in magic variables

| Variable | Meaning |
|----------|---------|
| `inventory_hostname` | Name in inventory |
| `groups` | Dict of group names → host lists |
| `group_names` | Groups current host belongs to |
| `hostvars` | All hosts' variables |
| `play_hosts` | Hosts in current play |
| `ansible_facts` | Facts namespace |

### Cross-host reference

```yaml
- ansible.builtin.debug:
    msg: "DB server IP is {{ hostvars['db1']['ansible_default_ipv4']['address'] }}"
```

## Registering command output

Capture task results for conditional follow-up:

```yaml
- name: Check node version
  ansible.builtin.command: node --version
  register: node_ver
  changed_when: false

- name: Display version
  ansible.builtin.debug:
    msg: "Node version: {{ node_ver.stdout }}"

- name: Fail if wrong major version
  ansible.builtin.fail:
    msg: "Expected Node 20"
  when: "'v20' not in node_ver.stdout"
```

### Register structure

```yaml
node_ver:
  stdout: "v20.11.0"
  stderr: ""
  rc: 0
  changed: false
```

## lookup plugins

```yaml
- ansible.builtin.authorized_key:
    user: deploy
    key: "{{ lookup('file', '~/.ssh/id_ed25519.pub') }}"
  when: lookup('file', '~/.ssh/id_ed25519.pub', errors='ignore') | length > 0
```

`lookup('file', ...)` reads control node file at playbook parse time.

## set_fact

Runtime variables (persist for host during play):

```yaml
- ansible.builtin.set_fact:
    effective_port: "{{ nodejs_app_port | int + 1000 }}"

- ansible.builtin.debug:
    msg: "Effective port {{ effective_port }}"
```

## vars_files

Load external variable files:

```yaml
- hosts: all
  vars_files:
    - vars/production.yml
    - vars/secrets.yml
```

## Variable naming conventions

- Lowercase with underscores: `nodejs_app_port`
- Prefix role variables: `webserver_port`, `nodejs_app_name`
- Boolean flags: `enable_firewall`, `install_optional`
- Avoid hyphens — use underscores

## Template best practices

1. **Keep logic minimal** — complex logic belongs in vars or filters
2. **Comment in Jinja2** — `{# this is a comment #}`
3. **Validate configs** — `validate:` parameter on template module
4. **Mode and ownership** — always set for sensitive files
5. **Notify handlers** — template changes trigger reload

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `VARIABLE IS NOT DEFINED` | Typo or wrong precedence | Check `ansible-inventory --host` |
| Template not found | Wrong path | `src` relative to templates/ |
| Empty output in template | Undefined var | Use `default` filter |
| Literal `{{` in output | Escape or use `{% raw %}` | See Jinja2 docs |
| Wrong port deployed | Extra var override | Check `-e` and group_vars |

## Role variable layers (Lab 08)

```
group_vars/all.yml          → all hosts
roles/common/defaults/      → common role defaults
roles/webserver/defaults/   → webserver_port: 80
play vars / -e              → overrides
```

Trace precedence when debugging unexpected values.

## Related documentation

- [Playbook Structure](playbook-structure.md)
- [Handlers and Notify](handlers-notify.md)
- [Gathering Facts](../facts/gathering-facts.md)
- [Lab 03 — Node.js](../../labmanuals/lab03-nodejs-playbook.md)
- [Lab 08 — Roles](../../labmanuals/lab08-roles-project.md)

## Quick reference

```yaml
# Variable use
{{ variable_name }}
{{ ansible_facts.distribution }}
{{ inventory_hostname }}

# Template task
- ansible.builtin.template:
    src: config.j2
    dest: /etc/app/config
    mode: "0644"

# Register
- command: cmd
  register: result
  changed_when: false

# Extra vars
ansible-playbook site.yml -e "key=value"
```

## Summary

Variables flow from defaults through group_vars to extra vars with clear precedence. Jinja2 templates in `templates/*.j2` render configuration from variables and facts. Use `register` for command output, filters for safe defaults, and role defaults for overridable parameters. Extended labs demonstrate templates for nginx, Node.js, and systemd units.

---

*Ansible Extended Track · Lesson 5 LEP · Curriculum v2*
