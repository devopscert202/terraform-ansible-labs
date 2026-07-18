# Playbooks and YAML Basics

## Objective (conceptual)

A **playbook** is a YAML file listing one or more **plays**. Each play maps **hosts** to **tasks** (module calls) and optional **handlers**. YAML indentation defines structure—two spaces per level is Ansible convention. Playbooks are the durable, reviewable artifact ad hoc commands grow into.

The mental model: a **play** is one act on a stage (host group); **tasks** are lines of the script; **handlers** are callbacks that run once when notified.

**Interactive reference:** [Playbooks and Handlers](../../html/playbook-handlers.html)

## Minimal playbook structure

```yaml
---
- name: Install and configure Apache
  hosts: webservers
  become: true
  tasks:
    - name: Install apache2
      ansible.builtin.apt:
        name: apache2
        state: present
        update_cache: true

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

| Key | Meaning |
|-----|---------|
| `---` | YAML document start (recommended) |
| `- name:` (play) | Human-readable play title |
| `hosts:` | Inventory pattern |
| `become: true` | Use sudo for tasks |
| `tasks:` | Ordered module invocations |
| `notify:` | Queue handler by exact name match |
| `handlers:` | Run at end of play if notified |

## YAML rules that trip beginners

- Indent with spaces only—never tabs.
- List items use leading `- ` at the same column.
- `name:` on tasks is **documentation**; it does not define a variable.
- Quote strings containing `:` or `{` to avoid parser surprises.

## Role entry playbook

```yaml
---
- name: Site with webserver role
  hosts: webservers
  become: true
  roles:
    - webserver
```

Roles package tasks, handlers, defaults, and templates (roles chapter).

## Check mode and diff

```bash
ansible-playbook playbooks/apache.yml --check --diff
```

`--check` asks modules to predict changes without applying (not all modules support it fully).

## Playbook vs ad hoc decision

| Ad hoc | Playbook |
|--------|----------|
| One module, quick test | Multiple related tasks |
| Not in git by default | Version controlled |
| No handlers | Handlers and roles |

## Syntax validation

```bash
ansible-playbook playbooks/apache.yml --syntax-check
```

Run before CI or long applies.

## Common playbook mistakes

| Mistake | Fix |
|---------|-----|
| Handler name typo vs `notify` | Names must match exactly |
| Forgot `become: true` | Add for package/service tasks |
| Wrong `hosts` pattern | `ansible-inventory --graph` |
| Non-FQCN module in exams | Use `ansible.builtin.*` |

## Import and reuse

`import_playbook` includes another playbook file at parse time—useful when `site.yml` grows large:

```yaml
- import_playbook: apache.yml
- import_playbook: vars-demo.yml
```

Essentials labs keep one file per exercise for clarity.

## Operational commands (reference)

```bash
cd ansible/essentials/labs
ansible-playbook playbooks/apache.yml --syntax-check
ansible-playbook playbooks/apache.yml --check
ansible-playbook playbooks/apache.yml
ansible-playbook playbooks/role-site.yml
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 04: Apache Webserver](../../labmanuals/lab04-playbook-apache-webserver.md) | Multi-task playbook, handlers, `become` |
| [Lab 06: Create Roles](../../labmanuals/lab06-roles-create.md) | Refactor playbook into a role |
