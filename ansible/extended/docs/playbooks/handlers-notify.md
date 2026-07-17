# Handlers and Notify

Handlers run **at the end of the play** (or when flushed) and only if notified.

## Pattern

```yaml
tasks:
  - name: Deploy config
    ansible.builtin.template:
      src: nginx.conf.j2
      dest: /etc/nginx/nginx.conf
    notify: Reload nginx

handlers:
  - name: Reload nginx
    ansible.builtin.service:
      name: nginx
      state: reloaded
```

## Rules

1. Handler `name` must **exactly** match `notify` (case-sensitive).
2. Multiple tasks can notify the same handler (runs once).
3. Use `ansible.builtin.meta: flush_handlers` to run handlers immediately.

## Changed vs notified

Handlers run only when the notifying task reports `changed`. A task that is `ok` (already correct) does not trigger handlers.

## Related lab

[lab06 — Handlers](../../labmanuals/lab06-handlers.md)
