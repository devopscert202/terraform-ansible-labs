# Dynamic Inventory on AWS EC2

## Objective (conceptual)

**Dynamic inventory** builds the host list at runtime from a cloud API instead of a static file. When instances launch or terminate, the next Ansible run sees the current fleet. The `amazon.aws.aws_ec2` inventory plugin filters by region, tags, and state, then maps EC2 attributes to Ansible variables.

The mental model: static inventory is a printed map; dynamic inventory is **GPS**—always current, but you need cloud credentials and tagging discipline.

**Interactive reference:** [Dynamic Inventory (AWS)](../../html/dynamic-inventory.html)

## Plugin configuration

`inventory/aws_ec2.yml`:

```yaml
---
# Dynamic inventory plugin for AWS EC2 (Lesson 6 AP-03)
# Requires: boto3, botocore on control node; IAM permissions or AWS_PROFILE
plugin: amazon.aws.aws_ec2
regions:
  - us-east-1
filters:
  instance-state-name: running
  tag:Environment: ansible-lab
keyed_groups:
  - key: tags.Role
    prefix: role
  - key: placement.region
    prefix: aws_region
hostnames:
  - private-ip-address
compose:
  ansible_host: private_ip_address
  ansible_user: "'ubuntu'"
```

## Configuration breakdown

| Key | Purpose |
|-----|---------|
| `plugin` | FQCN of inventory plugin |
| `regions` | Limit API queries |
| `filters` | EC2 API filters (state, tags) |
| `keyed_groups` | Auto-create groups like `role_web` from tags |
| `hostnames` | How inventory names appear |
| `compose` | Set `ansible_host`, `ansible_user` from EC2 fields |

## Prerequisites on control node

```bash
pip install boto3 botocore
export AWS_PROFILE=training
aws sts get-caller-identity
```

IAM needs `ec2:DescribeInstances` (and related read permissions) for targeted regions.

## Tagging contract

Instances should carry consistent tags:

- `Environment: ansible-lab` — matches `filters`
- `Role: web` or `Role: app` — feeds `keyed_groups`

Untagged or stopped instances disappear from inventory—by design.

## Running with dynamic inventory

```bash
ansible-inventory -i inventory/aws_ec2.yml --graph
ansible -i inventory/aws_ec2.yml role_web -m ansible.builtin.ping
ansible-playbook -i inventory/aws_ec2.yml playbooks/site.yml
```

## keyed_groups patterns

`tags.Role` with `prefix: role` creates `role_web`, `role_app` groups when tag `Role=web`. Playbooks can target `role_web` without maintaining host lists.

## Static fallback for hybrid ops

Keep a small static inventory for bastion or CI runners; merge with `ansible-inventory` export or separate plays. Labs focus on pure EC2 plugin usage.

## Pitfalls

| Issue | Fix |
|-------|-----|
| Empty inventory | Check tags, region, instance state |
| Permission denied | Verify IAM policy and `AWS_PROFILE` |
| Wrong SSH user | Adjust `compose.ansible_user` |
| Slow runs | Narrow `filters` and `regions` |

## Caching and performance

Dynamic inventory queries EC2 on every command unless caching is configured (`cache: true` with a plugin or `--cache` patterns in `ansible.cfg`). For large fleets, enable inventory cache with a short TTL to reduce API calls.

## Verifying keyed_groups

```bash
ansible-inventory -i inventory/aws_ec2.yml --graph | grep role_
ansible -i inventory/aws_ec2.yml role_web --list-hosts
```

Hosts missing expected tags will not appear in `role_*` groups—fix tags in AWS console or Terraform before blaming Ansible.

## Operational commands (reference)

```bash
cd ansible/extended/labs
ansible-inventory -i inventory/aws_ec2.yml --list
ansible-inventory -i inventory/aws_ec2.yml --host i-0abc123
ansible-playbook -i inventory/aws_ec2.yml playbooks/site.yml --limit role_app
aws ec2 describe-instances --filters "Name=tag:Environment,Values=ansible-lab"
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 07: Dynamic Inventory](../../labmanuals/lab07-dynamic-inventory.md) | EC2 plugin, keyed_groups, compose, ping web tier |
