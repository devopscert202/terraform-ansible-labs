# Lab 01: Static Host Inventory

> **Goal:** Ansible can reach your target servers using a static inventory file.
> **Time:** ~30 min · **Files:** `labs/inventory/hosts.ini`

## Before you start

- [AWS lab environment](../../../curriculum/setup/aws-lab-environment.md) complete
- SSH from control node to `web1` and `web2` works

## Steps

### Step 1 — Confirm Ansible on the control node

```bash
ansible --version
```

**Validate**

```text
ansible [core 2.
```

Major version 2.14 or newer is fine.

### Step 2 — Copy the inventory template

On the control node:

```bash
cd ~/terraform-ansible-labs/ansible/essentials/labs
cp inventory/hosts.ini.local.example inventory/hosts.ini.local
```

Edit `hosts.ini.local` and replace `10.0.1.10` / `10.0.1.11` with your web nodes' **private IPs**.

### Step 3 — Test connectivity

```bash
ansible -i inventory/hosts.ini.local webservers -m ansible.builtin.ping
```

**Validate**

```text
web1 | SUCCESS => { "ping": "pong" }
web2 | SUCCESS => { "ping": "pong" }
```

Both hosts return `pong`.

## Done when

- [ ] `ansible ... ping` succeeds on every host in `webservers`
- [ ] You know which file lists your hosts (`hosts.ini.local`)

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `UNREACHABLE` | SSH or wrong IP | `ssh ubuntu@<ip>` manually; fix security group port 22 |
| `Permission denied` | Key not copied | Run `ssh-copy-id` from setup guide |

## Cleanup

No resources to remove. Keep `hosts.ini.local` for the next lab.

---
*Source: Lesson 2 AP-01 · Next: [lab02](lab02-inventory-hosts-groups.md) · Deep dive: [inventory doc](../docs/02-inventory/inventory-ini-and-yaml.md)*
