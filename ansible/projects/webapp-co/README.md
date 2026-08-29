# WebApp Co — Shared Scenario

Fictional company used across Ansible and Terraform labs. Learners configure **web** and **db** tiers with Ansible, then provision supporting AWS resources with Terraform.

## Narrative

| Tier | Ansible group | Role |
|------|---------------|------|
| Web | `webservers` | Apache/nginx, Node.js capstone app |
| Database | `dbservers` | Placeholder for future DB automation |

## Ansible assets

- Inventory: [ansible/essentials/labs/inventory/hosts.ini](../../essentials/labs/inventory/hosts.ini)
- Capstone playbook: [ansible/essentials/labs/playbooks/nodejs.yml](../../essentials/labs/playbooks/nodejs.yml)

## Terraform assets

- EC2 pattern: [terraform/labs/lab03-first-ec2](../../../terraform/labs/lab03-first-ec2)
- VPC + EC2 capstone: [terraform/labmanuals/lab21-capstone-vpc-ec2.md](../../../terraform/labmanuals/lab21-capstone-vpc-ec2.md)

## Suggested flow

1. Ansible essentials lab01–lab07 (configure web tier)
2. Terraform Basic tier lab00–lab05 (credentials, providers, first EC2)
3. Terraform Intermediate tier lab06–lab12 (variables, state, modules)
4. Terraform Advanced tier lab13–lab21 (remote state, capstone VPC + EC2)
