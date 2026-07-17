# Lab 06: Ansible Roles

> **Goal:** Package tasks into a reusable role and run it from a playbook.
> **Time:** ~75 min · **Files:** `labs/roles/webserver/`, `labs/playbooks/role-site.yml`

## Before you start

- [lab05](lab05-playbook-variables.md) complete

## Steps

### Step 1 — Inspect the role layout

```bash
cd ~/terraform-ansible-labs/ansible/essentials/labs
find roles/webserver -type f
```

Expected: `tasks/main.yml`, `handlers/main.yml`, `defaults/main.yml`.

### Step 2 — Run the site playbook

```bash
ansible-playbook -i inventory/hosts.ini.local playbooks/role-site.yml
```

**Validate**

```text
failed=0
```

### Step 3 — Verify Apache on webservers

```bash
ansible webservers -i inventory/hosts.ini.local -b -m ansible.builtin.command -a "systemctl is-active apache2"
```

**Validate** — `active` on each host.

## Done when

- [ ] Role executes via `roles:` in playbook
- [ ] Service is running after role apply

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Role not found | Wrong path | Run playbook from `labs/` directory |

## Cleanup

Same as lab04 Apache cleanup.

---
*Source: Lesson 6 AP-01 · Next: [lab07](lab07-vault-and-nodejs-capstone.md) · Deep dive: [roles doc](../docs/06-roles/ansible-roles.md)*
