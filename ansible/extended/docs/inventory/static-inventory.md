# Static Inventory

INI and YAML formats list hosts and groups explicitly.

## INI example

```ini
[webservers]
web1 ansible_host=10.0.1.10

[webservers:vars]
ansible_user=ubuntu
```

## Verify

```bash
ansible-inventory -i inventory/hosts.ini --graph
ansible-inventory -i inventory/hosts.ini --list
```

## group_vars

Files in `group_vars/<groupname>.yml` attach variables to groups automatically when the inventory path is a directory or playbook references the group.

## Related

Essentials track: [inventory lab](../../../essentials/labmanuals/lab01-inventory-static-hosts.md)
