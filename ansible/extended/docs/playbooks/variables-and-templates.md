# Variables, Lookups, and Templates (Extended)

## Objective (conceptual)

Extended playbooks combine **inventory variables**, **group_vars**, **registers**, **lookups**, and **Jinja2 templates** to deploy real application stacks. Lookups fetch data at runtime from files, templates, or environment—without baking secrets into playbooks. Templates render `.j2` files into systemd units, nginx configs, and Node.js apps.

The mental model: variables answer *what values*; lookups answer *where to fetch them*; templates answer *how to render files on disk*.

**Interactive reference:** [Variables and Templates](../../../essentials/html/variables-templates.html)

## Layered variables

`group_vars/all.yml`:

```yaml
---
lab_environment: extended
nodejs_version: "20"
nodejs_app_port: 3000
nodejs_app_name: lab-app
```

Used in repository lines and paths:

```yaml
    - name: Add NodeSource apt repository
      ansible.builtin.apt_repository:
        repo: "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_{{ nodejs_version }}.x nodistro main"
        filename: nodesource
        state: present
```

## Template deployment

```yaml
    - name: Deploy application file
      ansible.builtin.template:
        src: app.js.j2
        dest: /opt/{{ nodejs_app_name }}/app.js
        owner: ubuntu
        group: ubuntu
        mode: "0644"
      notify: Restart nodejs app

    - name: Deploy systemd unit
      ansible.builtin.template:
        src: nodejs-app.service.j2
        dest: /etc/systemd/system/{{ nodejs_app_name }}.service
        mode: "0644"
      notify:
        - Reload systemd
        - Restart nodejs app
```

Templates live beside the playbook or in `roles/<role>/templates/`.

## file lookup for SSH keys

From `loops-packages.yml`:

```yaml
    - name: Authorize deploy user SSH key
      ansible.builtin.authorized_key:
        user: deploy
        key: "{{ lookup('file', '~/.ssh/id_ed25519.pub') }}"
        state: present
      when: lookup('file', '~/.ssh/id_ed25519.pub', errors='ignore') | length > 0
```

| Lookup | Purpose |
|--------|---------|
| `file` | Read local file on control node |
| `env` | Environment variable |
| `pipe` | Run command on control node (use carefully) |

## register variables

```yaml
    - name: Verify Node.js version
      ansible.builtin.command: node --version
      register: node_version
      changed_when: false

    - name: Display Node.js version
      ansible.builtin.debug:
        msg: "Node.js installed: {{ node_version.stdout }}"
```

Access fields: `stdout`, `stderr`, `rc`, `ansible_facts` (module-dependent).

## Jinja2 filters in extended plays

```yaml
msg: "Installed {{ baseline_packages | length }} packages on {{ inventory_hostname }}"
```

Common filters: `default`, `bool`, `upper`, `join`, `map`, `selectattr`.

## hostvars and inventory_hostname

```bash
ansible webservers -m ansible.builtin.debug -a "var=hostvars[inventory_hostname]"
```

Inspect merged variables per host during troubleshooting.

## Secrets with Vault

Extended Node.js capstone may combine templates with vault vars—decrypt at runtime:

```bash
ansible-playbook playbooks/nodejs.yml --vault-password-file ~/.ansible/vault-pass.txt
```

Never commit vault password files or plaintext production secrets.

## Operational commands (reference)

```bash
cd ansible/extended/labs
ansible-playbook playbooks/nodejs.yml --check --diff
ansible-playbook playbooks/loops-packages.yml -e "baseline_packages=['htop','curl']"
ansible-inventory --host app1
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Essentials Lab 05: Playbook Variables](../../../essentials/labmanuals/lab05-playbook-variables.md) | MOTD template and group_vars |
| [Lab 03: Node.js Playbook](../../labmanuals/lab03-nodejs-playbook.md) | Templates, registers, app variables |
| [Lab 04: Loops](../../labmanuals/lab04-loops.md) | `lookup('file', ...)` with conditionals |
