# Configuration Management and Infrastructure as Code

## Overview

Configuration management (CM) keeps servers and applications in a known, repeatable state. Instead of logging into each machine and running commands by hand, you describe the desired state in files and let a tool apply that state across many targets.

Infrastructure as Code (IaC) extends the same idea to cloud resources—networks, virtual machines, load balancers—using declarative files that can be versioned, reviewed, and automated in CI/CD.

Ansible focuses on **what should be true on each server** (packages installed, services running, files present). Terraform focuses on **what cloud resources should exist**. Together they form a common workflow: Terraform provisions infrastructure; Ansible configures it.

## Key concepts

- **Desired state** — You declare outcomes (`apache2` installed, port 80 open), not a sequence of shell commands.
- **Idempotency** — Running the same automation twice should not keep changing the system once it is correct.
- **Version control** — Playbooks and Terraform files live in Git so teams can review changes like application code.
- **Repeatability** — The same files build dev, test, and production with different variables.

## Diagram

See the [Ansible architecture interactive page](../html/ansible-architecture.html) for control node vs target servers.

## Example

A minimal “ensure a package is installed” idea in Ansible:

```yaml
- name: Install curl
  ansible.builtin.apt:
    name: curl
    state: present
```

The module checks whether `curl` is already installed before making changes.

## Hands-on labs

Start with [lab01 — static inventory](../../labmanuals/lab01-inventory-static-hosts.md) after completing the [AWS lab setup](../../../curriculum/setup/aws-lab-environment.md).

## Next steps

- [Ansible architecture](ansible-architecture.md)
- [Inventory formats](../02-inventory/inventory-ini-and-yaml.md)
