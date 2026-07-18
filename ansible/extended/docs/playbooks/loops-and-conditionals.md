# Loops and Conditionals in Playbooks

## Objective (conceptual)

**Loops** repeat a task for each item in a list or dict—install many packages, create many users—without copy-pasting YAML. **Conditionals** (`when`) skip or run tasks based on facts, variables, or group membership. Together they make one playbook work across OS families and host tiers.

The mental model: loops are **for-each**; conditionals are **if-statements**—both keep playbooks DRY and readable.

**Interactive reference:** [Loops and Conditionals](../../html/loops-conditionals.html)

## loop over packages and users

From `playbooks/loops-packages.yml`:

```yaml
---
- name: Manage packages and users with loops
  hosts: webservers
  become: true
  vars:
    baseline_packages:
      - htop
      - vim
      - curl
      - jq
    lab_users:
      - name: deploy
        groups: sudo
        shell: /bin/bash
      - name: monitor
        groups: adm
        shell: /bin/bash
  tasks:
    - name: Install baseline packages
      ansible.builtin.apt:
        name: "{{ item }}"
        state: present
        update_cache: true
      loop: "{{ baseline_packages }}"
      loop_control:
        label: "{{ item }}"

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

- `item` — current loop element.
- `loop_control.label` — shortens log output.

## when with facts and groups

From `playbooks/conditionals-os.yml`:

```yaml
- name: Install nginx on Debian family
  ansible.builtin.apt:
    name: nginx
    state: present
    update_cache: true
  when: ansible_facts.os_family == "Debian"

- name: Ensure nginx is running on webservers
  ansible.builtin.service:
    name: nginx
    state: started
    enabled: true
  when:
    - inventory_hostname in groups.get('webservers', [])
    - ansible_facts.os_family == "Debian"

- name: Report skipped hosts for app tier
  ansible.builtin.debug:
    msg: "{{ inventory_hostname }} is not in appservers — skipping app tasks"
  when: inventory_hostname not in groups.get('appservers', [])
```

List form of `when` is **AND**—all conditions must be true.

## Lookup in conditionals

```yaml
- name: Authorize deploy user SSH key
  ansible.builtin.authorized_key:
    user: deploy
    key: "{{ lookup('file', '~/.ssh/id_ed25519.pub') }}"
    state: present
  when: lookup('file', '~/.ssh/id_ed25519.pub', errors='ignore') | length > 0
```

`errors='ignore'` prevents failure when the pub key file is absent.

## loop vs with_items

Modern Ansible uses `loop:` — `with_items` is legacy alias. New playbooks should use `loop` only.

## Conditionals and check mode

Tasks skipped by `when: false` do not run in check mode either. Test both branches with `--limit` on representative hosts.

## Common patterns

| Goal | Pattern |
|------|---------|
| Debian vs RedHat | `when: ansible_facts.os_family == "Debian"` |
| Single host maintenance | `--limit web1` plus `when` guards |
| Feature flag | `when: enable_firewall \| bool` |
| Group-specific work | `inventory_hostname in groups['webservers']` |

## Operational commands (reference)

```bash
cd ansible/extended/labs
ansible-playbook playbooks/loops-packages.yml --check
ansible-playbook playbooks/conditionals-os.yml
ansible-playbook playbooks/conditionals-os.yml --limit web1
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 04: Loops](../../labmanuals/lab04-loops.md) | Package and user loops with `loop_control` |
| [Lab 05: Conditionals](../../labmanuals/lab05-conditionals.md) | OS family, group membership, firewall flag |
