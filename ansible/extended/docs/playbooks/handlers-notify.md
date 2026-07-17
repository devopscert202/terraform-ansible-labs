# Handlers and Notify

Handlers are special tasks that run **once at the end of the play** (unless flushed earlier) and only when notified by a changed task. They are essential for service reloads — restart nginx only when configuration actually changes, not on every playbook run. Lab 06 implements this pattern in `handlers-nginx.yml`.

## Learning objectives

- Define handlers and trigger them with `notify`
- Understand changed vs ok and handler execution rules
- Use `meta: flush_handlers` for mid-play reloads
- Avoid handler name mismatch bugs
- Validate handler behavior in playbook output

## Why handlers exist

Without handlers, every playbook run would restart services:

```yaml
# Anti-pattern — restarts every run
- ansible.builtin.template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf

- ansible.builtin.service:
    name: nginx
    state: restarted   # Always runs — causes downtime
```

With handlers:

```yaml
- ansible.builtin.template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
  notify: Reload nginx

handlers:
  - name: Reload nginx
    ansible.builtin.service:
      name: nginx
      state: reloaded
```

Handler runs only when template reports `changed`.

## Handler execution flow

```
Task with notify runs
         │
         ▼
    changed: true? ──no──► Handler queued but NOT executed (ok/skipped task)
         │
        yes
         ▼
    Handler queued
         │
         ▼
    All tasks in play complete
         │
         ▼
    RUNNING HANDLER [Handler name]
         │
         ▼
    Handler tasks execute (once per handler name)
```

## Basic pattern

From `labs/playbooks/handlers-nginx.yml`:

```yaml
---
- name: Configure nginx with handlers
  hosts: webservers
  become: true
  tasks:
    - name: Install nginx
      ansible.builtin.apt:
        name: nginx
        state: present

    - name: Deploy lab site config
      ansible.builtin.template:
        src: nginx-lab.conf.j2
        dest: /etc/nginx/sites-available/lab.conf
        mode: "0644"
        validate: nginx -t -f %s
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

## Handler rules

### Rule 1: Exact name match

`notify` string must **exactly** match handler `name` — case-sensitive:

```yaml
notify: Reload nginx    # ✓ matches handler name: Reload nginx
notify: reload nginx    # ✗ silent failure — handler never runs
notify: Restart nginx   # ✗ different word — handler never runs
```

Lab 09 Drill 03 demonstrates this failure mode — play succeeds but service not reloaded.

### Rule 2: Changed tasks only

| Task result | Handler notified? |
|-------------|-------------------|
| `changed` | Yes |
| `ok` (already correct) | No |
| `skipped` | No |
| `failed` | No (play stops) |

Second playbook run: template `ok` → no handler execution.

### Rule 3: Handlers run once

Multiple tasks notifying the same handler → handler executes **once** at end of play.

```yaml
# Both notify same handler — Reload nginx runs once
- template: ... notify: Reload nginx
- file: ... notify: Reload nginx
```

### Rule 4: End of play execution

Handlers run after all tasks in the current play unless flushed.

## flush_handlers

Force immediate handler execution mid-play:

```yaml
- name: Deploy config
  ansible.builtin.template:
    src: nginx-lab.conf.j2
    dest: /etc/nginx/sites-available/lab.conf
  notify: Reload nginx

- name: Apply handlers now
  ansible.builtin.meta: flush_handlers

- name: Verify HTTP response
  ansible.builtin.uri:
    url: http://127.0.0.1/
    return_content: true
  register: http_result
```

Without flush, URI test might run before nginx reloads.

## Handler use cases

| Scenario | Handler action |
|----------|----------------|
| Config file change | `state: reloaded` (graceful) |
| Application deploy | `state: restarted` |
| systemd daemon-reload | `ansible.builtin.systemd: daemon_reload: true` |
| Cache invalidation | Custom script via `command` |

Prefer `reloaded` over `restarted` when service supports it — less disruptive.

## Multiple handlers

```yaml
tasks:
  - ansible.builtin.template:
      src: app.conf.j2
      dest: /etc/app/app.conf
    notify:
      - Reload app
      - Clear cache

handlers:
  - name: Reload app
    ansible.builtin.service:
      name: app
      state: reloaded

  - name: Clear cache
    ansible.builtin.command: /opt/app/clear-cache.sh
```

## listen directive (alias)

Multiple notify names can trigger one handler:

```yaml
handlers:
  - name: Reload nginx
    listen: "nginx config changed"
    ansible.builtin.service:
      name: nginx
      state: reloaded

tasks:
  - template: ...
    notify: "nginx config changed"
```

## Handlers in roles

Role handlers live in `roles/<name>/handlers/main.yml`:

```yaml
# roles/webserver/handlers/main.yml
---
- name: Reload webserver
  ansible.builtin.service:
    name: nginx
    state: reloaded
```

Tasks in `roles/webserver/tasks/main.yml` notify by name. Handlers aggregate at play level when role is applied.

Lab 08 `webserver` role uses handler on template change.

## changed_when override

Force notification even when module reports ok:

```yaml
- ansible.builtin.command: /opt/custom-reload.sh
  register: reload_result
  changed_when: true   # Always notify
  notify: Reload app
```

Use sparingly — defeats idempotency checks.

## Debugging handlers

### Look for RUNNING HANDLER

```text
RUNNING HANDLER [Reload nginx] *************************
changed: [web1]
changed: [web2]
```

Absent on second idempotent run — expected.

### Handler not running checklist

1. Compare `notify` and handler `name` character-by-character
2. Did notifying task report `changed`?
3. Did play fail before handler phase?
4. Is handler in same play (not different play)?

### Test with intentional change

```bash
# Edit template, add comment line
ansible-playbook -i inventory/hosts.ini playbooks/handlers-nginx.yml
# Expect: template changed + RUNNING HANDLER
```

## Handlers vs inline service restart

| Approach | Pros | Cons |
|----------|------|------|
| Handler | Idempotent, no unnecessary restarts | Name matching gotcha |
| Inline restart | Simple | Restarts every run |
| `register` + `when` | Explicit control | Verbose |

Production: always prefer handlers for service lifecycle.

## validate with template module

Prevent deploying broken configs:

```yaml
- ansible.builtin.template:
    src: nginx-lab.conf.j2
    dest: /etc/nginx/sites-available/lab.conf
    validate: nginx -t -f %s
  notify: Reload nginx
```

`%s` replaced with temp file path — nginx tests before copy.

## Extended lab workflow

```bash
cd ~/terraform-ansible-labs/ansible/extended/labs

# First run — expect handler
ansible-playbook -i inventory/hosts.ini playbooks/handlers-nginx.yml

# Second run — no handler
ansible-playbook -i inventory/hosts.ini playbooks/handlers-nginx.yml

# Verify site
ansible -i inventory/hosts.ini web1 -m uri -a "url=http://127.0.0.1/ return_content=yes"
```

## Break-fix connection

Drill 03 (`drill-03-handler-mismatch.yml`):

```yaml
notify: restart nginx      # lowercase restart
handlers:
  - name: Restart nginx   # uppercase Restart — MISMATCH
```

Fix: align strings exactly.

## Related documentation

- [Playbook Structure](playbook-structure.md)
- [Variables and Templates](variables-and-templates.md)
- [Lab 06 — Handlers](../../labmanuals/lab06-handlers.md)
- [Lab 09 — Break-Fix](../../labmanuals/lab09-break-fix-drills.md)

## Quick reference

```yaml
tasks:
  - name: Deploy config
    ansible.builtin.template:
      src: file.j2
      dest: /etc/service/config
    notify: Handler exact name

  - ansible.builtin.meta: flush_handlers

handlers:
  - name: Handler exact name
    ansible.builtin.service:
      name: service
      state: reloaded
```

## Summary

Handlers defer service actions until end of play and run only when notifying tasks change state. Match `notify` to handler `name` exactly, use `flush_handlers` when subsequent tasks depend on reload, and verify with `RUNNING HANDLER` in output. Lab 06 and role-based Lab 08 demonstrate production handler patterns.

---

*Ansible Extended Track · Lesson 5 AP-05 · Curriculum v2*
