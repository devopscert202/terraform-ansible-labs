# Configuration Management and Infrastructure as Code

> **Curriculum:** Ansible Essentials · **Brand:** `#EE0000` · **Lab targets:** Ubuntu 22.04 · **SSH:** port 22

## Overview

Modern platform engineering separates **provisioning** (creating servers, networks, storage) from **configuration** (installing software, applying settings, deploying applications). This curriculum teaches both halves: Terraform for Infrastructure as Code (IaC) and Ansible for Configuration Management (CM).

**Infrastructure as Code** expresses cloud resources in declarative files versioned in Git. **Configuration management** ensures running systems match a declared desired state—repeatedly and predictably—without manual SSH sessions.

Together, Terraform and Ansible form a pipeline: Terraform builds the environment; Ansible makes each host production-ready. Neither replaces the other; they complement different layers of the stack.

**Interactive reference:** [ansible-architecture.html](../../html/ansible-architecture.html)

---

## Key Concepts

### IaC vs Configuration Management

| Dimension | Infrastructure as Code (Terraform) | Configuration Management (Ansible) |
|-----------|----------------------------------|-------------------------------------|
| **Primary question** | What infrastructure exists? | What state should each host be in? |
| **Typical resources** | VPC, subnets, EC2, RDS, S3 | Packages, services, config files, users |
| **Execution model** | Provider API calls to cloud | SSH (agentless) to hosts |
| **State** | Terraform state file | Desired state in playbooks (no CMDB required) |
| **Idempotency** | Plan shows create/change/destroy | Modules report `changed` or `ok` |
| **This repo** | `terraform/essentials/labs/` | `ansible/essentials/labs/` |

### Declarative vs Imperative

| Style | Description | Example |
|-------|-------------|---------|
| **Declarative** | Define end state; tool figures out steps | `state: present` in `ansible.builtin.apt` |
| **Imperative** | Define exact sequence of commands | Shell script: `apt update && apt install apache2` |
| **Ansible default** | Declarative modules | Prefer modules over `ansible.builtin.shell` |
| **When imperative** | Procedural logic needed | `ansible.builtin.command` with explicit args |

### Configuration Drift

| Concept | Definition | Tool response |
|---------|------------|---------------|
| **Drift** | Live system differs from intended config | Re-run playbook to converge |
| **Detection** | Compare actual vs desired | `ansible-playbook --check` (dry run) |
| **Remediation** | Apply missing changes | Normal playbook run |
| **Prevention** | Scheduled Ansible from CI/CD | Pipeline runs on merge to main |

---

## The Two-Tool Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        VERSION CONTROL (Git)                            │
│   terraform/essentials/labs/          ansible/essentials/labs/          │
└───────────────┬─────────────────────────────────┬───────────────────────┘
                │                                 │
                ▼                                 ▼
        ┌───────────────┐                 ┌───────────────┐
        │   Terraform   │                 │    Ansible    │
        │  terraform    │                 │ ansible-      │
        │  apply        │                 │ playbook      │
        └───────┬───────┘                 └───────┬───────┘
                │                                 │
                ▼                                 ▼
        ┌───────────────┐                 ┌───────────────┐
        │  AWS API      │                 │  SSH :22      │
        │  (provision)  │                 │  (configure)  │
        └───────┬───────┘                 └───────┬───────┘
                │                                 │
                └────────────┬────────────────────┘
                             ▼
                    ┌─────────────────┐
                    │  Ubuntu 22.04   │
                    │  EC2 instances  │
                    │  web1, web2, db1│
                    └─────────────────┘
```

### Responsibility Split in the Lab

| Layer | Tool | Artifact | Outcome |
|-------|------|----------|---------|
| Network | Terraform | `main.tf`, `variables.tf` | VPC, subnets, routes |
| Compute | Terraform | EC2 resource blocks | Running VMs |
| Access | Terraform | Key pair, security groups | SSH on port 22 allowed |
| Inventory | Ansible | `inventory/hosts.ini` | Host-to-IP mapping |
| Software | Ansible | `playbooks/apache.yml` | Apache installed |
| Secrets | Ansible Vault | `vault/secrets.yml` | Encrypted credentials |
| Reuse | Ansible Roles | `roles/webserver/` | Packaged web tier logic |

---

## Why Ansible for Configuration?

### Agentless Architecture

Traditional CM tools installed daemons on every server. Ansible uses **existing SSH** and temporary Python execution:

```
Control Node                    Managed Node (Ubuntu 22.04)
────────────                    ────────────────────────────
ansible-playbook  ──SSH:22──►   sshd accepts connection
       │                        Python runs module, exits
       ◄── JSON result ──        No permanent agent process
```

Benefits: simpler security model, no agent upgrades, works with any SSH-accessible host.

### Push Model

Ansible **pushes** configuration from the control node. Alternatives (Puppet, Chef) often use pull agents. Push fits CI/CD pipelines where a runner executes playbooks after Terraform apply.

### Human-Readable YAML

Playbooks are reviewable in pull requests. Compare a 20-line playbook to a 200-line bash script for the same Apache install—the playbook wins on clarity and idempotency.

---

## Configuration Management Patterns

| Pattern | Description | Lab example |
|---------|-------------|-------------|
| **Baseline** | OS packages, users, SSH hardening | `ansible.builtin.apt` in `apache.yml` |
| **Application deploy** | Install runtime, deploy code | `playbooks/nodejs.yml` |
| **Templating** | Generate config from variables | `templates/motd.j2` + `vars-demo.yml` |
| **Orchestration** | Multi-tier ordered changes | `role-site.yml` with `webserver` role |
| **Secrets injection** | Encrypted vars at runtime | `vault/secrets.yml` in `nodejs.yml` |

---

## FQCN Module Examples

### Package Management (Desired State)

```yaml
- name: Ensure Apache is installed
  ansible.builtin.apt:
    name: apache2
    state: present
    update_cache: true
```

`state: present` is declarative: the module ensures the package exists, whether or not it was already installed.

### Service Management

```yaml
- name: Ensure Apache is running
  ansible.builtin.service:
    name: apache2
    state: started
    enabled: true
```

### File Templating

```yaml
- name: Deploy MOTD
  ansible.builtin.template:
    src: ../templates/motd.j2
    dest: /etc/motd
    mode: "0644"
```

Template `motd.j2` references `{{ inventory_hostname }}`, `{{ app_env }}`, and `{{ webserver_port }}` from inventory and group vars.

### Privilege Escalation

```yaml
- name: Install and configure Apache
  hosts: webservers
  become: true    # uses sudo per ansible.cfg
  tasks:
    - name: Install apache2
      ansible.builtin.apt:
        name: apache2
        state: present
```

---

## GitOps and Pipeline Integration

```
Developer ──► PR ──► CI Pipeline
                        │
            ┌───────────┼───────────┐
            ▼           ▼           ▼
      terraform plan  ansible-    security
                      lint        scan
            │           │
            ▼           ▼
      terraform apply  ansible-playbook
      (on merge)       (on merge)
```

| Stage | Validation command |
|-------|-------------------|
| Lint Terraform | `terraform fmt -check` |
| Validate Terraform | `terraform validate` |
| Lint Ansible | `ansible-lint playbooks/` |
| Syntax check | `ansible-playbook playbooks/apache.yml --syntax-check` |
| Dry run | `ansible-playbook playbooks/apache.yml --check` |

---

## Comparison with Manual Administration

| Task | Manual (SSH + apt) | Ansible playbook |
|------|-------------------|------------------|
| Install Apache on 2 web servers | SSH twice, run commands twice | One `ansible-playbook` run |
| Document what was done | Separate runbook | Playbook *is* the documentation |
| Repeat after rebuild | Remember all steps | Re-run same playbook |
| Audit trail | Shell history (maybe) | Git commit + CI logs |
| Rollback | Manual uninstall | Version-controlled playbook revert |

---

## Immutable vs Mutable Infrastructure

| Approach | Philosophy | Tool emphasis |
|----------|------------|---------------|
| **Mutable** | Update servers in place | Ansible configures running VMs |
| **Immutable** | Replace servers on change | Terraform creates new instances; Ansible bootstraps once |
| **Hybrid (lab)** | Terraform replaces infra; Ansible converges config | Best of both for learning |

In production, teams often combine: golden AMIs built with Ansible/Packer, orchestrated by Terraform, with Ansible for day-2 drift correction.

---

## Variable and Secret Hierarchy Preview

Configuration values flow from multiple sources (covered in depth in [Ansible Variables](../05-variables/ansible-variables.md)):

```
CLI -e extra vars  (highest precedence)
        ▼
playbook vars / vars_files
        ▼
inventory group_vars / host_vars
        ▼
role defaults  (lowest precedence)
```

Lab file `inventory/group_vars/webservers.yml`:

```yaml
webserver_port: 80
app_env: production
```

These values feed templates and conditionals across playbooks.

---

## Troubleshooting

| Symptom | Layer | Likely cause | Fix |
|---------|-------|--------------|-----|
| Instances exist but Ansible fails | Handoff | Inventory IPs stale after Terraform rebuild | Update `hosts.ini` from Terraform outputs |
| Terraform apply succeeds, nothing configured | Process | Skipped Ansible step | Run `ansible-playbook` after apply |
| Config reverts after manual edit | CM model | Expected—re-run playbook to converge | Treat playbook as source of truth |
| Different results on two hosts | Drift | One host manually modified | Run playbook with `--diff` to compare |
| Playbook works locally, fails in CI | Environment | CI missing SSH key or vault password | Inject secrets via CI variables |
| `changed=0` but service broken | Module limits | Package present ≠ service healthy | Add `ansible.builtin.service` + handlers |
| Terraform destroys, Ansible errors | Lifecycle | Inventory points to terminated hosts | Refresh inventory after destroy/apply |

### Validation Workflow

```bash
# 1. Provision (from terraform labs directory)
terraform apply

# 2. Update inventory with new IPs
# Edit ansible/essentials/labs/inventory/hosts.ini

# 3. Verify connectivity
cd ansible/essentials/labs
ansible all -m ansible.builtin.ping

# 4. Configure
ansible-playbook playbooks/apache.yml
```

---

## Hands-on Labs

| Lab | Focus | Manual |
|-----|-------|--------|
| Prerequisites | AWS environment setup | [aws-lab-environment.md](../../../../curriculum/setup/aws-lab-environment.md) |
| Lab 01 | Inventory basics | [lab01-inventory-static-hosts.md](../../labmanuals/lab01-inventory-static-hosts.md) |
| Lab 04 | First playbook (Apache) | [lab04-playbook-apache-webserver.md](../../labmanuals/lab04-playbook-apache-webserver.md) |
| Lab 07 | Vault + Node.js capstone | [lab07-vault-and-nodejs-capstone.md](../../labmanuals/lab07-vault-and-nodejs-capstone.md) |

**HTML companions:**

- [ansible-architecture.html](../../html/ansible-architecture.html)
- [adhoc-vs-playbook.html](../../html/adhoc-vs-playbook.html)

---

## Best Practices Summary

| Practice | Rationale |
|----------|-----------|
| Version control everything | Audit, rollback, collaboration |
| Separate repos or paths for TF and Ansible | Clear ownership boundaries |
| Use FQCN modules | Explicit, future-proof module references |
| Prefer roles for reuse | `roles/webserver/` encapsulates web tier |
| Encrypt secrets with Vault | Never commit plaintext `api_token` |
| Run `--check` before production changes | Preview impact |
| Pin Ansible and collection versions | Reproducible pipelines |

---

## Next Steps

1. Deep dive into [Ansible Architecture](ansible-architecture.md) for control node, inventory, and module execution details.
2. Configure [Inventory: INI and YAML](../02-inventory/inventory-ini-and-yaml.md) to match your Terraform-provisioned hosts.
3. Run Lab 04 to experience declarative configuration with `playbooks/apache.yml`.
4. Progress through variables, roles, and vault modules to complete the essentials track.

---

## Glossary

| Term | Definition |
|------|------------|
| **IaC** | Infrastructure as Code—machine-readable infra definitions |
| **CM** | Configuration Management—automated system state enforcement |
| **Idempotent** | Operation safe to repeat without side effects |
| **Convergence** | Process of bringing system to desired state |
| **Control node** | Machine running Ansible commands |
| **Managed node** | Target host being configured |
| **Playbook** | YAML file defining automation plays |
| **FQCN** | Fully Qualified Collection Name for modules |
