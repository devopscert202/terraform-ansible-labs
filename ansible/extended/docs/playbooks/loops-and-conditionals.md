# Loops and Conditionals

## Loops

Use `loop` with a list variable:

```yaml
- name: Install packages
  ansible.builtin.apt:
    name: "{{ item }}"
    state: present
  loop:
    - curl
    - jq
  loop_control:
    label: "{{ item }}"
```

`loop_control.label` keeps output readable on large lists.

## Conditionals

Use `when` for branching:

```yaml
- name: Install nginx on Debian
  ansible.builtin.apt:
    name: nginx
    state: present
  when: ansible_facts.os_family == "Debian"
```

Combine conditions:

```yaml
when:
  - enable_firewall | bool
  - inventory_hostname in groups['webservers']
```

## Facts in conditionals

Gather facts first (default) or selectively:

```yaml
- ansible.builtin.setup:
    gather_subset:
      - distribution
```

## Related labs

- [lab04 — Loops](../../labmanuals/lab04-loops.md)
- [lab05 — Conditionals](../../labmanuals/lab05-conditionals.md)
