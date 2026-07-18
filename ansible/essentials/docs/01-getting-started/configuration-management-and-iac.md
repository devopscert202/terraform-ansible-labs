# Configuration Management and Infrastructure as Code

## Objective (conceptual)

**Configuration management (CM)** keeps servers and applications in a known desired state—packages installed, files present, services running—across reboots and scaling events. **Infrastructure as Code (IaC)** provisions networks, VMs, and cloud primitives from versioned files. In modern platforms, Terraform (or cloud APIs) builds the machines; Ansible configures them afterward.

The mental model: IaC answers *what exists*; CM answers *how it behaves*. Together they replace snowflake servers built by console clicks and undocumented shell history.

**Interactive reference:** [Ansible Architecture](../../html/ansible-architecture.html)

## Why configuration management

| Without CM | With Ansible |
|------------|--------------|
| SSH in and run commands manually | Playbook reruns identically |
| Drift between servers | Same role on every `webservers` host |
| No audit trail | Git history of YAML changes |
| Slow onboarding | New engineer runs one playbook |

Ansible modules are **idempotent**: running the same task twice should not break a host that already matches desired state.

## CM vs IaC boundaries

| Concern | Typical tool | Example |
|---------|--------------|---------|
| VPC, subnet, security group | Terraform | `aws_vpc` |
| OS packages, app config | Ansible | `ansible.builtin.apt`, `template` |
| Container image contents | Dockerfile / build pipeline | Not Ansible on host |
| Kubernetes desired state | Helm / manifests | Often not Ansible |

Lab 04 installs Apache with Ansible on hosts Terraform or a cloud console may have created.

## Declarative play excerpt

```yaml
---
- name: Install and configure Apache
  hosts: webservers
  become: true
  tasks:
    - name: Install apache2
      ansible.builtin.apt:
        name: apache2
        state: present
        update_cache: true

    - name: Enable mod_rewrite
      ansible.builtin.apache2_module:
        name: rewrite
        state: present
      notify: Restart apache2

  handlers:
    - name: Restart apache2
      ansible.builtin.service:
        name: apache2
        state: restarted
```

Describe **state: present**—not "run apt install".

## Version control and review

- Store playbooks, inventory examples, and roles in git.
- Use pull requests for production changes.
- Pair CM repos with CI: `ansible-playbook --syntax-check`, molecule, or check mode in pipelines.

## Immutable vs mutable infrastructure

- **Mutable** — Keep the VM; Ansible updates packages in place (essentials track focus).
- **Immutable** — Replace the whole image/instance on change; Ansible may bake the image (Packer) instead of patching live servers.

Know which pattern your organization uses; playbooks look similar but run frequency differs.

## When Ansible is the wrong tool

- Real-time orchestration with complex event graphs (consider messaging or operators).
- High-frequency state reconciliation on thousands of nodes without strategy (consider image-based deploys).
- Provisioning net-new cloud networking (use Terraform first).

## Idempotency in practice

Run the Apache playbook twice—the second run should report `ok` on package install if apache2 is already present, not `changed` every time. If a task always shows `changed`, the module parameters may be wrong or the resource drifts outside Ansible's detection.

```bash
ansible-playbook playbooks/apache.yml
ansible-playbook playbooks/apache.yml   # second run — mostly ok
```

## Git layout for CM repos

```
ansible/essentials/labs/
├── ansible.cfg
├── inventory/
├── playbooks/
├── roles/
└── group_vars/
```

Keep inventory examples in git; exclude `*.local` files with real IPs via `.gitignore`.

## Drift detection with CM

Schedule periodic `ansible-playbook site.yml --check` in CI to report drift—tasks that would change indicate manual edits on servers. Pair with Terraform plan for infrastructure-layer drift.

## Operational commands (reference)

```bash
cd ansible/essentials/labs
ansible-playbook playbooks/apache.yml --check --diff
ansible-playbook playbooks/apache.yml
ansible-playbook playbooks/apache.yml --list-tasks
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 04: Apache Webserver Playbook](../../labmanuals/lab04-playbook-apache-webserver.md) | First multi-task playbook with handlers |
| [Lab 07: Vault and Node.js Capstone](../../labmanuals/lab07-vault-and-nodejs-capstone.md) | CM plus secrets for an application stack |
