# Custom Ansible Facts

## Objective (conceptual)

**Custom facts** extend discovery with site-specific data—datacenter rack, cost center, application tier—without stuffing everything into inventory hostnames. Place executable or JSON files under `/etc/ansible/facts.d/` on managed nodes; Ansible loads them as `ansible_facts.ansible_local.*` on the next `setup` run.

The mental model: default facts describe **the machine**; custom facts describe **your organization's metadata** about that machine.

**Interactive reference:** [Facts and Custom Facts](../../html/facts.html)

## Fact file locations

| Path | Behavior |
|------|----------|
| `/etc/ansible/facts.d/*.fact` | Executable; stdout must be JSON |
| `/etc/ansible/facts.d/*.json` | Static JSON read as-is |

After deployment, run `setup` or start a play to refresh.

## JSON custom fact example

Deploy `/etc/ansible/facts.d/site.json`:

```json
{
  "tier": "web",
  "cost_center": "CC-4401",
  "backup_window": "02:00-04:00 UTC"
}
```

Reference in playbooks:

```yaml
- name: Show site tier
  ansible.builtin.debug:
    msg: "Tier={{ ansible_facts.ansible_local.site.tier }}"
```

Key path includes filename (`site`) without extension.

## Executable fact script example

`/etc/ansible/facts.d/datacenter.fact` (mode `0755`):

```bash
#!/bin/bash
echo '{"dc":"us-east-1a","row":"R12"}'
```

Must print valid JSON to stdout—no extra logging lines.

## Deploying facts with Ansible

```yaml
- name: Install custom fact file
  ansible.builtin.copy:
    dest: /etc/ansible/facts.d/site.json
    mode: "0644"
    content: |
      {
        "tier": "web",
        "lab": "extended"
      }

- name: Refresh facts after custom fact install
  ansible.builtin.setup:
    gather_subset:
      - "!all"
      - ansible_local
```

## Custom facts vs inventory vars

| Custom facts | Inventory / group_vars |
|--------------|------------------------|
| Lives on managed node | Lives on control node |
| Survives if inventory regenerated | Requires inventory update |
| Good for agentless metadata discovery | Good for connection vars (`ansible_host`) |

Use inventory for **how to connect**; custom facts for **what the node reports about itself**.

## Custom facts vs set_fact

- `ansible.builtin.set_fact` — variables for **current play** only (unless cached).
- Custom facts in `facts.d` — persist on disk across Ansible runs.

## Pitfalls

| Issue | Fix |
|-------|-----|
| Invalid JSON | Validate with `python3 -m json.tool` |
| Script not executable | `mode: "0755"` on `.fact` files |
| Stale facts after edit | Re-run `setup` or play |
| Wrong key path | Filename becomes `ansible_local.<name>` |

## Testing custom facts locally

On the managed node (SSH session):

```bash
sudo /etc/ansible/facts.d/datacenter.fact
python3 -m json.tool /etc/ansible/facts.d/site.json
```

Invalid output breaks `setup` for that host—validate before wide rollout.

## Combining with templates

Custom facts can drive Jinja in templates:

```jinja2
Datacenter: {{ ansible_facts.ansible_local.datacenter.dc | default('unknown') }}
```

Use `default` when custom facts may be absent on some hosts.

## Operational commands (reference)

```bash
cd ansible/extended/labs
ansible web1 -m ansible.builtin.setup -a "filter=ansible_local*"
ansible web1 -m ansible.builtin.command -a "cat /etc/ansible/facts.d/site.json"
ansible-playbook playbooks/conditionals-os.yml --limit web1
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 02: Working with Facts](../../labmanuals/lab02-facts.md) | Deploy custom facts to `/etc/ansible/facts.d/` and query `ansible_local` |
