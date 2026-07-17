# Variables and Templates

## Variable precedence (simplified)

1. Extra vars (`-e`)
2. Task vars
3. Block vars
4. Role defaults
5. Inventory `group_vars` / `host_vars`

## Jinja2 in templates

```jinja2
server_name {{ inventory_hostname }};
listen {{ webserver_port }};
```

## Registering command output

```yaml
- ansible.builtin.command: node --version
  register: node_ver
  changed_when: false
```

## Related labs

- [lab03 — Node.js](../../labmanuals/lab03-nodejs-playbook.md)
- [lab08 — Roles](../../labmanuals/lab08-roles-project.md)
