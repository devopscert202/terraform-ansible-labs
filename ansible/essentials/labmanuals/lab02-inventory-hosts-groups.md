# Lab 02: Hosts and Groups

> **Goal:** Organize servers into groups and attach group variables.
> **Time:** ~30 min · **Files:** `labs/inventory/hosts.yaml`, `labs/inventory/group_vars/webservers.yml`

## Before you start

- [lab01](lab01-inventory-static-hosts.md) complete

## Steps

### Step 1 — Review the YAML inventory

```bash
cd ~/terraform-ansible-labs/ansible/essentials/labs
cat inventory/hosts.yaml
```

Groups separate **webservers** from **dbservers**. Update IP addresses to match your environment.

### Step 2 — List hosts per group

```bash
ansible-inventory -i inventory/hosts.yaml --graph
```

**Validate**

```text
@webservers:
  |--web1
  |--web2
@dbservers:
  |--db1
```

### Step 3 — Use group variables

```bash
ansible webservers -i inventory/hosts.yaml -m ansible.builtin.debug -a "var=webserver_port"
```

**Validate**

```text
"webserver_port": 80
```

Each web host reports `webserver_port` from `inventory/group_vars/webservers.yml`.

## Done when

- [ ] `--graph` shows expected groups
- [ ] Group variable `webserver_port` appears in debug output

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| YAML parse error | Indentation | Use spaces only; align under `hosts:` |
| Variable undefined | Wrong group name | Host must be in `webservers` group |

## Cleanup

None.

---
*Source: Lesson 2 AP-02 · Next: [lab03](lab03-adhoc-commands.md) · Deep dive: [inventory doc](../docs/02-inventory/inventory-ini-and-yaml.md)*
