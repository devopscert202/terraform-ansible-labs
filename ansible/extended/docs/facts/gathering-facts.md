# Gathering Ansible Facts

## Objective (conceptual)

**Facts** are variables Ansible discovers about each managed host—OS family, memory, IP addresses, mount points. The `ansible.builtin.setup` module collects them (often automatically at play start). Facts power **conditionals** (`when: ansible_facts.os_family == "Debian"`) and templates without hard-coding per host.

The mental model: facts are **automatic inventory enrichment**—Ansible SSHs in, runs small Python snippets, and caches results for the play.

**Interactive reference:** [Facts and Custom Facts](../../html/facts.html)

## Default fact gathering

At play start Ansible runs `setup` unless `gather_facts: false`. Access modern keys via `ansible_facts`:

```yaml
- name: Report OS
  ansible.builtin.debug:
    msg: "{{ ansible_facts.distribution }} {{ ansible_facts.distribution_version }}"
```

Legacy `ansible_distribution` still works on many versions; prefer `ansible_facts.*` in new playbooks.

## Selective gathering

Reduce noise and time on large fleets:

```yaml
- name: Gather minimal facts when needed
  ansible.builtin.setup:
    gather_subset:
      - "!all"
      - distribution
      - distribution_version
```

Extended `conditionals-os.yml` uses this pattern before OS-specific package tasks.

## Useful fact keys

| Fact | Example use |
|------|-------------|
| `ansible_facts.os_family` | Choose `apt` vs `yum` |
| `ansible_facts.distribution` | Display name (Ubuntu, Rocky) |
| `ansible_facts.default_ipv4.address` | Bind address, firewall rules |
| `ansible_facts.memtotal_mb` | Capacity checks |
| `ansible_facts.mounts` | Disk planning |

## Ad hoc fact commands

```bash
ansible web1 -m ansible.builtin.setup
ansible webservers -m ansible.builtin.setup -a "filter=ansible_distribution*"
ansible all -m ansible.builtin.setup --tree /tmp/facts
```

`--tree` writes one file per host under `/tmp/facts/` for offline inspection.

## Facts in conditionals

From `conditionals-os.yml`:

```yaml
- name: Install nginx on Debian family
  ansible.builtin.apt:
    name: nginx
    state: present
    update_cache: true
  when: ansible_facts.os_family == "Debian"
```

Facts must exist before the `when` evaluates—gather subset or rely on play-level fact gathering.

## Disabling facts

```yaml
- name: Fast play without facts
  hosts: webservers
  gather_facts: false
  tasks:
    - name: ...
```

Use when every task is fact-independent and speed matters.

## Fact caching (concept)

`fact_caching` in `ansible.cfg` can persist facts between runs (JSON file or Redis). Essentials labs use default in-memory facts per play. Enable caching only when fact gathering dominates runtime and staleness is acceptable.

## Debugging fact issues

```bash
ansible web1 -m ansible.builtin.setup -a "gather_subset=min"
ansible-playbook playbooks/conditionals-os.yml -vvv | grep -i fact
```

If `when` clauses skip unexpectedly, verify facts exist on the host (`ansible_facts` empty when gathering disabled).

## Fact injection for tests

`ansible-playbook` with `--extra-vars` can mock facts in check mode for dry runs—advanced pattern; labs use real `setup` on live VMs.

## ansible_facts network subset

```bash
ansible web1 -m ansible.builtin.setup -a "gather_subset=network"
```

Smaller fact payload when only IP and interface data is needed for firewall or bind tasks.

## Operational commands (reference)

```bash
cd ansible/extended/labs
ansible -i inventory/hosts.ini web1 -m ansible.builtin.setup -a "filter=ansible_memtotal_mb"
ansible-playbook playbooks/conditionals-os.yml --check
ansible-doc ansible.builtin.setup
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 02: Working with Facts](../../labmanuals/lab02-facts.md) | Gather, filter, debug facts; custom facts intro |
| [Lab 05: Conditionals](../../labmanuals/lab05-conditionals.md) | Branch tasks with `ansible_facts` and groups |
