# Handlers and notify

## Objective (conceptual)

**Handlers** are tasks that run **only when notified**, typically once at the end of the play, after regular tasks change configuration. They prevent restarting a service six times when six template tasks update files. **notify** links a task to a handler by **exact name match**.

The mental model: tasks **stage** work; handlers **commit** side effects like service reloads.

**Interactive reference:** [Playbooks and Handlers](../../../essentials/html/playbook-handlers.html)

## Essentials pattern: Apache restart

```yaml
    - name: Enable mod_rewrite
      ansible.builtin.apache2_module:
        name: rewrite
        state: present
      notify: Restart apache2

  handlers:
    - name: Restart apache2
      ansible.builtin.service:
        name: apache2
        state: restarted
```

If the module reports `changed`, the handler queues; otherwise notification is ignored.

## Extended pattern: nginx reload

From `playbooks/handlers-nginx.yml`:

```yaml
    - name: Deploy nginx configuration
      ansible.builtin.template:
        src: nginx-lab.conf.j2
        dest: /etc/nginx/sites-available/lab.conf
        mode: "0644"
        validate: nginx -t -c /etc/nginx/nginx.conf
      notify: Reload nginx

    - name: Enable lab site
      ansible.builtin.file:
        src: /etc/nginx/sites-available/lab.conf
        dest: /etc/nginx/sites-enabled/lab.conf
        state: link
      notify: Reload nginx

  handlers:
    - name: Reload nginx
      ansible.builtin.service:
        name: nginx
        state: reloaded
```

Multiple tasks may notify the same handler—Ansible deduplicates so **Reload nginx** runs once.

## Flush handlers early

```yaml
    - name: Force handler flush for validation
      ansible.builtin.meta: flush_handlers

    - name: Verify nginx responds locally
      ansible.builtin.uri:
        url: http://127.0.0.1/
        return_content: true
      register: nginx_response
      changed_when: false
```

Use `flush_handlers` when later tasks depend on handler side effects (config applied, service reloaded).

## Multiple notifications

```yaml
      notify:
        - Reload systemd
        - Restart nodejs app
```

Both handlers queue if the task changes.

## Handler rules

| Rule | Detail |
|------|--------|
| Name match | `notify: Reload nginx` must equal handler `name:` |
| End of play | Default flush after all tasks in play |
| Only `changed` | `ok` or `skipped` tasks do not notify |
| Listen alias | `listen: restart web` groups handlers (advanced) |

## restart vs reloaded

| State | Effect |
|-------|--------|
| `restarted` | Stop then start (dropped connections) |
| `reloaded` | Graceful config reload when daemon supports it |

Prefer `reloaded` for nginx/apache when only config changed.

## Break-fix: handler mismatch

Lab 09 drills include wrong handler names—symptom: config updates but service serves stale content. Fix `notify` string or handler `name:`.

## Operational commands (reference)

```bash
cd ansible/extended/labs
ansible-playbook playbooks/handlers-nginx.yml
ansible-playbook playbooks/handlers-nginx.yml --check --diff
ansible-playbook playbooks/apache.yml   # essentials comparison
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Essentials Lab 04: Apache Webserver](../../../essentials/labmanuals/lab04-playbook-apache-webserver.md) | First handler with service restart |
| [Extended Lab 06: Handlers](../../labmanuals/lab06-handlers.md) | nginx template, reload, `flush_handlers`, URI check |
| [Lab 09: Break-Fix Drills](../../labmanuals/lab09-break-fix-drills.md) | Fix handler name mismatches |
