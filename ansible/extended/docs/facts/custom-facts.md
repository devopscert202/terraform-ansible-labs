# Custom Facts

Place executable scripts or `.fact` files in `/etc/ansible/facts.d/` on managed nodes.

## Example: static fact file

`/etc/ansible/facts.d/lab.fact`:

```ini
[lab]
tier=web
environment=extended
```

After creation, facts appear under `ansible_local`:

```yaml
- ansible.builtin.debug:
    var: ansible_local.lab.tier
```

## Deploy with Ansible

```yaml
- ansible.builtin.copy:
    dest: /etc/ansible/facts.d/lab.fact
    content: |
      [lab]
      tier=web
    mode: "0755"
```

Re-gather facts or run `setup` to refresh.

## Related lab

[lab02 — Facts](../../labmanuals/lab02-facts.md)
