# Loops and Conditionals

Loops repeat tasks across list items; conditionals skip or include tasks based on expressions. Together they eliminate duplicated YAML and enable fact-driven, portable playbooks. Extended labs 04 and 05 implement these patterns in `loops-packages.yml` and `conditionals-os.yml`.

## Learning objectives

- Use `loop` with lists and dictionaries
- Configure `loop_control` for readable output
- Write `when` expressions with facts and group membership
- Combine multiple conditions with AND logic
- Choose between loops and conditionals appropriately

## Loop fundamentals

### Basic package loop

From `labs/playbooks/loops-packages.yml`:

```yaml
vars:
  baseline_packages:
    - htop
    - vim
    - curl
    - jq

tasks:
  - name: Install baseline packages
    ansible.builtin.apt:
      name: "{{ item }}"
      state: present
      update_cache: true
    loop: "{{ baseline_packages }}"
    loop_control:
      label: "{{ item }}"
```

### Execution model

```
baseline_packages = [htop, vim, curl, jq]
         │
         ▼
Task runs 4 times, item = each package
         │
         ▼
Each iteration: ansible.builtin.apt name=htop, then vim, etc.
```

The magic variable `item` holds the current iteration value.

## Loop types comparison

| Syntax | Status | Item variable | Best for |
|--------|--------|---------------|----------|
| `loop:` | Current standard | `item` | All new playbooks |
| `loop_control:` | Recommended add-on | Custom label, index | Large lists |
| `with_items:` | Legacy | `item` | Migrate to `loop` |
| `with_dict:` | Legacy | `item.key`, `item.value` | Use `dict2items` filter |
| `until:` + `retries:` | Retry pattern | Same task repeated | Wait for readiness |

### Migration from with_items

```yaml
# Legacy
- ansible.builtin.apt:
    name: "{{ item }}"
  with_items:
    - curl
    - jq

# Modern
- ansible.builtin.apt:
    name: "{{ item }}"
  loop:
    - curl
    - jq
```

## Loop over dictionaries

`lab_users` in loops-packages.yml:

```yaml
lab_users:
  - name: deploy
    groups: sudo
    shell: /bin/bash
  - name: monitor
    groups: adm
    shell: /bin/bash

- name: Create lab users
  ansible.builtin.user:
    name: "{{ item.name }}"
    groups: "{{ item.groups }}"
    shell: "{{ item.shell }}"
    create_home: true
  loop: "{{ lab_users }}"
  loop_control:
    label: "{{ item.name }}"
```

Access dict keys via `item.name`, `item.groups`, etc.

### Dict from variable with dict2items

```yaml
- name: Create directories from dict
  ansible.builtin.file:
    path: "{{ item.value }}"
    state: directory
  loop: "{{ directory_map | dict2items }}"
  loop_control:
    label: "{{ item.key }}"
```

## loop_control options

```yaml
loop_control:
  label: "{{ item }}"           # Output display (not variable value)
  index_var: my_idx             # Expose 0-based index as my_idx
  pause: 2                      # Seconds between iterations
  extended_allitems: true       # Nested loop: allitems list
```

Without `label`, Ansible prints full JSON for each item — unreadable on large lists.

## Nested loops

```yaml
- name: Create users in multiple groups
  ansible.builtin.user:
    name: "{{ item.0 }}"
    groups: "{{ item.1 }}"
  loop: "{{ users | product(groups) | list }}"
```

Prefer `include_tasks` with outer loop for complex nesting.

## Retry loops (until)

Different from list iteration — retries the **same** task:

```yaml
- name: Wait for application port
  ansible.builtin.uri:
    url: "http://127.0.0.1:3000/health"
    status_code: 200
  register: result
  until: result.status == 200
  retries: 12
  delay: 5
```

## Conditionals with when

### OS family branching

From `conditionals-os.yml`:

```yaml
- name: Install nginx on Debian family
  ansible.builtin.apt:
    name: nginx
    state: present
  when: ansible_facts.os_family == "Debian"
```

Ubuntu reports `Debian` family — this task runs on Ubuntu 22.04.

### Group membership

```yaml
- name: Configure web tier index page
  ansible.builtin.template:
    src: index.html.j2
    dest: /var/www/html/index.html
  when: inventory_hostname in groups['webservers']
```

### Feature flags

```yaml
- name: Allow SSH through UFW
  community.general.ufw:
    rule: allow
    port: "22"
    proto: tcp
  when: enable_firewall | bool
```

Run with flag:

```bash
ansible-playbook conditionals-os.yml -e "enable_firewall=false"
# UFW task shows: skipping
```

## Multiple conditions (AND)

All conditions must be true:

```yaml
when:
  - enable_firewall | bool
  - ansible_facts.os_family == "Debian"
  - inventory_hostname in groups['webservers']
```

## OR and complex logic

```yaml
# OR — use parentheses in Jinja2
when: ansible_facts.os_family == "Debian" or ansible_facts.os_family == "RedHat"

# NOT
when: inventory_hostname not in groups['appservers']

# Defined check
when: optional_var is defined
```

## Loop + when combined

```yaml
- name: Install optional packages
  ansible.builtin.apt:
    name: "{{ item }}"
    state: present
  loop: "{{ optional_packages }}"
  when: install_optional | default(false) | bool
```

Entire loop skipped when condition false.

Per-item condition inside loop:

```yaml
- ansible.builtin.apt:
    name: "{{ item }}"
  loop: "{{ packages }}"
  when: item != 'skip-me'
```

## Conditionals with registered results

```yaml
- ansible.builtin.command: systemctl is-active nginx
  register: nginx_status
  changed_when: false
  failed_when: false

- ansible.builtin.debug:
    msg: "nginx is running"
  when: nginx_status.rc == 0
```

## Facts in conditionals

Ensure facts exist before use:

```yaml
# Default: facts gathered at play start
- hosts: all
  tasks:
    - ansible.builtin.apt:
        name: nginx
      when: ansible_facts.os_family == "Debian"

# Manual gather when gather_facts: false
- hosts: all
  gather_facts: false
  tasks:
    - ansible.builtin.setup:
        gather_subset:
          - distribution
    - ansible.builtin.apt:
        name: nginx
      when: ansible_facts.os_family == "Debian"
```

## Debugging conditionals

Verbose output shows why tasks skip:

```bash
ansible-playbook -i inventory/hosts.ini playbooks/conditionals-os.yml -v
```

```text
skipping: [web1] => (item=...)  => (item=...)  when condition false
```

Temporary debug:

```yaml
- ansible.builtin.debug:
    var: ansible_facts.os_family
```

## Loop vs when decision guide

| Need | Use |
|------|-----|
| Same module, many items | `loop` |
| Skip entire task | `when` |
| Different modules per OS | Separate tasks with `when` |
| Optional feature | `when` with boolean flag |
| Retry until success | `until` |

## Extended lab exercises

### Lab 04 validation

```bash
ansible-playbook -i inventory/hosts.ini playbooks/loops-packages.yml
ansible -i inventory/hosts.ini web1 -b -m command -a "dpkg -l htop jq | tail -2"
```

### Lab 05 validation

```bash
ansible-playbook -i inventory/hosts.ini playbooks/conditionals-os.yml
ansible -i inventory/hosts.ini webservers -b -m command -a "systemctl is-active nginx"
```

## Common mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| `{{ item }}` in wrong context | undefined variable | Only inside loop task |
| Wrong indent under loop | YAML error | Task keys align with `name` |
| `when: var` without bool filter | Unexpected skip | Use `var \| bool` |
| Comparing os_family to Ubuntu | Task skips on Ubuntu | Use `Debian` family |
| Legacy with_items | Deprecation warning | Migrate to `loop` |

## Performance notes

- Large loops (1000+ items) — consider `throttle` or batch modules
- `loop_control.pause` — rate-limit API calls
- Combine packages into single apt task when possible:

```yaml
- ansible.builtin.apt:
    name: "{{ baseline_packages }}"
    state: present
```

Single apt call vs loop — both valid; loop shows iteration pedagogy.

## Related resources

- [Playbook Structure](playbook-structure.md)
- [Gathering Facts](../facts/gathering-facts.md)
- [Lab 04 — Loops](../../labmanuals/lab04-loops.md)
- [Lab 05 — Conditionals](../../labmanuals/lab05-conditionals.md)
- [loops-conditionals.html](../../html/loops-conditionals.html)

## Quick reference

```yaml
# Loop
loop: "{{ list_var }}"
loop_control:
  label: "{{ item }}"

# When
when: ansible_facts.os_family == "Debian"
when: inventory_hostname in groups['webservers']
when:
  - condition_one
  - condition_two
```

## Summary

Use `loop` to iterate lists and dicts with `item` as the current value. Use `when` for branching on facts, groups, and flags. Combine `loop_control.label` for readable output and verbose mode for skip debugging. Extended labs demonstrate package/user loops and OS-aware conditionals.

---

*Ansible Extended Track · Lesson 5 AP-03/AP-04 · Curriculum v2*
