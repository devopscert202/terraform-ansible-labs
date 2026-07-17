# Gathering Facts

Ansible collects **facts** about each host via the `setup` module (automatic by default).

## Common facts

| Fact | Example |
|------|---------|
| `ansible_hostname` | web1 |
| `ansible_distribution` | Ubuntu |
| `ansible_distribution_version` | 22.04 |
| `ansible_os_family` | Debian |
| `ansible_memtotal_mb` | 976 |

## Ad hoc

```bash
ansible webservers -m ansible.builtin.setup -a "filter=ansible_distribution*"
```

## Disable gathering

```yaml
- hosts: all
  gather_facts: false
```

Use when facts are not needed (faster runs).

## Related lab

[lab02 — Facts](../../labmanuals/lab02-facts.md)
