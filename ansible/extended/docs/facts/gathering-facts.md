# Gathering Facts

Ansible collects **facts** about each managed host at the start of every play (unless disabled). Facts are variables prefixed with `ansible_` that describe hardware, network, operating system, and environment. Understanding the fact gathering pipeline is essential for writing portable playbooks that adapt to different hosts without hard-coded values.

## Learning objectives

After reading this guide and completing Lab 02, you should be able to:

- Explain when and how Ansible gathers facts
- Run the `setup` module ad hoc with filters and subsets
- Reference common facts in tasks and templates
- Disable or limit fact gathering for performance
- Troubleshoot fact-related failures (Python interpreter, permissions)

## What are facts?

Facts are **discovered variables** — Ansible does not require you to define them in inventory. The `ansible.builtin.setup` module (historically called "setup") connects to each host and collects data into the `ansible_facts` namespace.

| Concept | Description |
|---------|-------------|
| Fact | A key-value pair about a host (e.g., `ansible_memtotal_mb: 976`) |
| `setup` module | Collects facts; runs automatically when `gather_facts: true` |
| `ansible_facts` | Dictionary containing all facts for the current host |
| Legacy access | `ansible_hostname` still works; equivalent to `ansible_facts.hostname` |

Facts power conditionals (`when: ansible_facts.os_family == "Debian"`), Jinja2 templates (`{{ ansible_default_ipv4.address }}`), and dynamic inventory compose rules.

## The fact gathering pipeline

```
Play starts
    │
    ▼
gather_facts: true? ──no──► Skip setup (no ansible_* facts unless manually gathered)
    │
   yes
    ▼
SSH/connect to host
    │
    ▼
setup module executes (Python on target required)
    │
    ▼
Collect subsets: hardware, network, distribution, mounts, etc.
    │
    ▼
Merge into ansible_facts / hostvars
    │
    ▼
Tasks execute with fact variables available
```

### Automatic gathering

By default, every play gathers facts before the first task:

```yaml
---
- name: Default behavior
  hosts: webservers
  # gather_facts: true  (implicit default)
  tasks:
    - ansible.builtin.debug:
        msg: "{{ ansible_facts.distribution }} {{ ansible_facts.distribution_version }}"
```

### Manual gathering

Run setup explicitly when facts were disabled or need refresh:

```yaml
- name: Refresh facts mid-play
  ansible.builtin.setup:

- name: Gather only distribution facts
  ansible.builtin.setup:
    gather_subset:
      - "!all"
      - distribution
```

### Disabling gathering

Use `gather_facts: false` when facts are not needed — common in container orchestration or network device plays:

```yaml
---
- name: Fast configuration play
  hosts: switches
  gather_facts: false
  tasks:
    - ansible.builtin.raw: show version
```

**Trade-off:** Without facts, `when` clauses referencing `ansible_os_family` will fail unless you run setup manually.

## Ad hoc fact commands

From the control node in `ansible/extended/labs/`:

```bash
# All facts on one host (large JSON output)
ansible -i inventory/hosts.ini web1 -m ansible.builtin.setup

# Filter by glob pattern
ansible -i inventory/hosts.ini webservers \
  -m ansible.builtin.setup -a "filter=ansible_distribution*"

# Multiple filters (comma-separated)
ansible -i inventory/hosts.ini web1 \
  -m ansible.builtin.setup -a "filter=ansible_distribution*,ansible_memtotal_mb"

# Minimal output — hostname only
ansible -i inventory/hosts.ini webservers \
  -m ansible.builtin.setup -a "filter=ansible_hostname"
```

### Validating ad hoc output

Expected distribution filter output on Ubuntu 22.04:

```json
{
    "ansible_facts": {
        "ansible_distribution": "Ubuntu",
        "ansible_distribution_version": "22.04",
        "ansible_distribution_release": "jammy",
        "ansible_distribution_major_version": "22"
    },
    "changed": false
}
```

## Common facts reference

### Operating system

| Fact | Example (Ubuntu 22.04) | Use case |
|------|--------------------------|----------|
| `ansible_hostname` | web1 | Short hostname in templates |
| `ansible_fqdn` | web1.lab.local | SSL certificates, logging |
| `ansible_distribution` | Ubuntu | OS-specific messaging |
| `ansible_distribution_version` | 22.04 | Version pinning decisions |
| `ansible_distribution_release` | jammy | Codename-based repo URLs |
| `ansible_os_family` | Debian | Package manager selection |
| `ansible_architecture` | x86_64 | Binary download URLs |

**Important:** Ubuntu reports `ansible_os_family: Debian`, not `Ubuntu`. Use `os_family` for package tasks, `distribution` for display.

### Hardware and memory

| Fact | Example | Use case |
|------|---------|----------|
| `ansible_processor_vcpus` | 2 | Thread pool sizing |
| `ansible_processor_cores` | 1 | Licensing |
| `ansible_memtotal_mb` | 976 | JVM heap, cache sizing |
| `ansible_memfree_mb` | 412 | Capacity monitoring |
| `ansible_devices` | dict of block devices | Disk provisioning |

### Network

| Fact | Example | Use case |
|------|---------|----------|
| `ansible_default_ipv4.address` | 10.0.1.10 | Bind address, firewall rules |
| `ansible_default_ipv4.gateway` | 10.0.1.1 | Routing configuration |
| `ansible_default_ipv4.interface` | ens5 | Interface-specific tasks |
| `ansible_all_ipv4_addresses` | list | Multi-homed hosts |

Access nested facts with dot notation or brackets:

```yaml
- ansible.builtin.debug:
    msg: "Primary IP is {{ ansible_facts['default_ipv4']['address'] }}"
```

### Python environment

| Fact | Example | Use case |
|------|---------|----------|
| `ansible_python_version` | 3.10.12 | Module compatibility |
| `ansible_python.executable` | /usr/bin/python3 | Interpreter debugging |

## gather_subset options

Control how much data setup collects. Smaller subsets = faster plays on large inventories.

```yaml
- ansible.builtin.setup:
    gather_subset:
      - "!all"          # Exclude everything first
      - min             # Minimal facts
      - distribution    # OS information
      - network         # Interfaces and IPs
```

### Available subsets

| Subset | Contents |
|--------|----------|
| `all` | Everything (default when no subset specified) |
| `min` | Minimal fact set |
| `hardware` | CPU, memory, devices |
| `network` | Interfaces, IPs, DNS |
| `virtual` | Virtualization type |
| `ohai` | Ohai-style data (if available) |
| `facter` | Facter data (if available) |
| `distribution` | OS name, version, family |

Prefix with `!` to exclude: `!hardware` skips hardware collection.

### Performance example

```yaml
---
- name: OS-only facts for package selection
  hosts: all
  gather_facts: false
  tasks:
    - name: Gather distribution only
      ansible.builtin.setup:
        gather_subset:
          - "!all"
          - distribution

    - name: Install packages on Debian
      ansible.builtin.apt:
        name: curl
        state: present
      when: ansible_facts.os_family == "Debian"
```

## Using facts in playbooks

### Debug output

```yaml
- name: Display host summary
  ansible.builtin.debug:
    msg: >-
      {{ inventory_hostname }} runs
      {{ ansible_facts.distribution }}
      {{ ansible_facts.distribution_version }}
      with {{ ansible_facts.processor_vcpus }} vCPUs
```

### Conditionals

```yaml
- name: Install nginx on Debian family
  ansible.builtin.apt:
    name: nginx
    state: present
  when: ansible_facts.os_family == "Debian"

- name: Install nginx on Red Hat family
  ansible.builtin.dnf:
    name: nginx
    state: present
  when: ansible_facts.os_family == "RedHat"
```

### Templates

```jinja2
{# templates/motd.j2 #}
Welcome to {{ ansible_hostname }}
OS: {{ ansible_distribution }} {{ ansible_distribution_version }}
Memory: {{ ansible_memtotal_mb }} MB
```

## Fact caching (production)

In development labs, facts are re-gathered every play. Production environments often enable caching in `ansible.cfg`:

```ini
[defaults]
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible_facts
fact_caching_timeout = 86400
```

| Setting | Effect |
|---------|--------|
| `gathering = smart` | Skip fact gather if cache valid |
| `fact_caching_timeout` | Seconds before cache expires |
| `jsonfile` | Simple file-based cache plugin |

The extended lab `ansible.cfg` does **not** enable caching — facts refresh each run by design.

## Troubleshooting

### setup module fails with Python error

**Symptom:** `/usr/bin/python: not found`

**Fix:** Set interpreter in inventory:

```ini
[webservers:vars]
ansible_python_interpreter=/usr/bin/python3
```

### Empty filter results

**Symptom:** setup returns minimal JSON without expected keys

**Fix:** Verify filter glob pattern includes asterisk: `filter=ansible_distribution*`

### Facts undefined in task

**Symptom:** `'ansible_os_family' is undefined`

**Causes:**
- `gather_facts: false` without manual setup
- Typo in variable name (use `ansible_facts.os_family` in Ansible 2.10+)
- Task runs before setup in play with `gather_facts: false`

### Permission errors on fact collection

Rare on Linux — setup runs as connected user. If using `become`, facts still gather as original user unless configured otherwise.

## Security considerations

Facts may contain sensitive data (IP addresses, mount points, user lists). Avoid logging full fact dumps in production CI output. Use filters when debugging:

```bash
ansible web1 -m setup -a "filter=ansible_distribution*" 2>/dev/null
```

## Best practices

1. **Use `os_family` for package managers** — covers Ubuntu, Debian, RHEL, CentOS consistently
2. **Filter ad hoc gathers** — avoid dumping 200KB JSON per host
3. **Disable when unnecessary** — network devices, Windows with slow WMI
4. **Re-gather after infrastructure changes** — new NIC, OS upgrade mid-playbook
5. **Prefer facts over hard-coded IPs** — `ansible_default_ipv4.address` for bind addresses

## Lab exercises cross-reference

| Lab step | Skill practiced |
|----------|-----------------|
| Lab 02 Step 1 | Full fact gather ad hoc |
| Lab 02 Step 2 | Filter with glob |
| Lab 02 Step 5 | Compare os_family across groups |
| Lab 02 Step 10 | gather_subset selective gather |
| Lab 05 | Facts in when conditionals |
| Lab 08 | Facts in role templates |

## Quick reference commands

```bash
# Graph inventory (prerequisite — verify hosts)
ansible-inventory -i inventory/hosts.ini --graph

# Distribution facts only
ansible webservers -i inventory/hosts.ini -m ansible.builtin.setup \
  -a "filter=ansible_distribution*"

# Print single fact via debug
ansible web1 -i inventory/hosts.ini -m ansible.builtin.setup -a "filter=ansible_hostname"
ansible web1 -i inventory/hosts.ini -m ansible.builtin.debug \
  -a "var=hostvars[inventory_hostname]['ansible_hostname']"

# Playbook with facts disabled
grep -n gather_facts playbooks/*.yml
```

## Related documentation

- [Custom Facts](custom-facts.md) — extending facts with `/etc/ansible/facts.d/`
- [Loops and Conditionals](../playbooks/loops-and-conditionals.md) — using facts in `when`
- [Lab 02 — Facts](../../labmanuals/lab02-facts.md) — hands-on exercises
- Interactive reference: [facts.html](../../html/facts.html)

## Summary

Facts are Ansible's mechanism for **discovering host state** rather than declaring it. The setup module runs automatically, populates `ansible_facts`, and enables portable automation. Filter and subset gathering for performance; disable when facts add no value; always set `ansible_python_interpreter` on modern Ubuntu hosts.

---

*Ansible Extended Track · Lesson 3 AP-03 · Last updated: curriculum v2*
