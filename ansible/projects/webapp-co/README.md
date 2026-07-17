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

- EC2 pattern: [terraform/essentials/labs/lab02-ec2](../../essentials/labs/lab02-ec2)
- Module capstone: [terraform/extended/labmanuals/lab15-capstone-projects.md](../../extended/labmanuals/lab15-capstone-projects.md)

## Suggested flow

1. Ansible essentials lab01–lab07 (configure web tier)
2. Terraform essentials lab01–lab08 (provision infra)
3. Optional extended tracks for depth
