# Lab 05: Variables and Templates

> **Goal:** Use group variables and a Jinja template in a playbook.
> **Time:** ~45 min · **Files:** `labs/playbooks/vars-demo.yml`, `labs/templates/motd.j2`

## Before you start

- [lab04](lab04-playbook-apache-webserver.md) complete

## Steps

### Step 1 — Review variables

```bash
cat ~/terraform-ansible-labs/ansible/essentials/labs/inventory/group_vars/webservers.yml
```

`webserver_port` and `app_env` apply to all hosts in `webservers` (from `inventory/group_vars/webservers.yml`).

### Step 2 — Run the demo playbook

```bash
cd ~/terraform-ansible-labs/ansible/essentials/labs
ansible-playbook -i inventory/hosts.ini.local playbooks/vars-demo.yml
```

**Validate**

```text
failed=0
```

### Step 3 — Check rendered template on web1

```bash
ansible web1 -i inventory/hosts.ini.local -m ansible.builtin.command -a "cat /etc/motd"
```

**Validate** — Output includes `app_env=production` (or your `app_env` value).

## Done when

- [ ] Playbook uses variables from `inventory/group_vars`
- [ ] Template file deployed to `/etc/motd`

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Undefined variable | Host not in group | Confirm host under `webservers` in inventory |

## Cleanup

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.file -a "path=/etc/motd state=absent"
```

---
*Source: Lesson 5 AP-02 · Next: [lab06](lab06-roles-create.md) · Deep dive: [variables doc](../docs/05-variables/ansible-variables.md)*
