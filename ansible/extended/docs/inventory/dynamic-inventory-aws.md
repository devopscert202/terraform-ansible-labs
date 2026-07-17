# Dynamic Inventory on AWS

Dynamic inventory builds host lists and groups from live cloud API data at runtime. When EC2 instances launch, terminate, or change tags, your next Ansible command reflects current state — no manual `hosts.ini` edits. This guide covers the `amazon.aws.aws_ec2` plugin used in `labs/inventory/aws_ec2.yml`.

## Learning objectives

- Configure the AWS EC2 inventory plugin
- Apply filters and keyed_groups for automatic group assignment
- Compose host variables from instance metadata
- Verify inventory and troubleshoot empty results
- Run playbooks against dynamic groups

## Why dynamic inventory?

| Scenario | Static inventory pain | Dynamic solution |
|----------|----------------------|------------------|
| Auto Scaling Group | IPs change constantly | API returns current instances |
| Terraform apply | New resources each run | Tag-based discovery |
| Multi-region fleet | Multiple INI files | Single plugin with regions list |
| Ephemeral dev environments | Stale entries | Filter by Environment tag |

Static inventory (`hosts.ini`) remains valid for fixed lab VMs. Lab 07 adds AWS dynamic inventory as a production pattern.

## Architecture overview

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Control Node   │────►│  Inventory Plugin │────►│   AWS EC2 API   │
│  ansible -i     │     │  amazon.aws.aws_ec2│     │ DescribeInstances│
│  aws_ec2.yml    │     └──────────────────┘     └─────────────────┘
└─────────────────┘              │                         │
                                 ▼                         ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │  boto3 / botocore │     │  EC2 Instances  │
                        │  AWS credentials  │     │  tags, IPs, AZ  │
                        └──────────────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  Inventory JSON   │
                        │  groups + hostvars│
                        └──────────────────┘
```

## Prerequisites

### Python packages

```bash
pip install boto3 botocore
python3 -c "import boto3; print('boto3', boto3.__version__)"
```

### Ansible collection

```bash
ansible-galaxy collection install amazon.aws
ansible-galaxy collection list amazon.aws
```

### AWS credentials

```bash
export AWS_PROFILE=lab-terraform
export AWS_DEFAULT_REGION=us-east-1

aws sts get-caller-identity --profile lab-terraform
```

Required IAM permission (minimum): `ec2:DescribeInstances`

### Network requirements

- Control node must reach instance **private IPs** if using VPC-internal addressing
- Security group allows SSH (22) from control node
- Same VPC or VPN/peering for private IP access

## Plugin configuration

Full configuration from extended labs:

```yaml
---
# labs/inventory/aws_ec2.yml
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

## Configuration keys explained

### `plugin`

Must be the fully qualified collection name:

```yaml
plugin: amazon.aws.aws_ec2
```

Legacy `ec2.py` script inventory is deprecated — use the plugin.

### `regions`

List of AWS regions to query. Omitting regions searches all regions (slow). Lab uses:

```yaml
regions:
  - us-east-1
```

### `filters`

Passed directly to EC2 `DescribeInstances`. Only matching instances appear in inventory.

```yaml
filters:
  instance-state-name: running
  tag:Environment: ansible-lab
  tag:Role: webservers   # optional additional filter
```

| Filter | Effect |
|--------|--------|
| `instance-state-name: running` | Exclude stopped/terminated |
| `tag:Environment: ansible-lab` | Only tagged lab instances |
| `vpc-id: vpc-abc123` | Limit to one VPC |

### `keyed_groups`

Automatically create Ansible groups from instance attributes:

```yaml
keyed_groups:
  - key: tags.Role
    prefix: role
```

Instance with `Role=webservers` tag joins group `role_webservers`.

Additional examples:

```yaml
keyed_groups:
  - key: instance_type
    prefix: type
  - key: placement.availability_zone
    prefix: az
  - key: tags.Environment
    prefix: env
```

### `hostnames`

How hosts appear in inventory output:

```yaml
hostnames:
  - private-ip-address
```

Alternatives: `ip-address`, `dns-name`, `tag:Name`, instance ID.

### `compose`

Set Ansible host variables from instance fields using Jinja2:

```yaml
compose:
  ansible_host: private_ip_address
  ansible_user: "'ubuntu'"
  instance_id: instance_id
  env_tag: tags.Environment
```

Note: string literals need quotes in compose — `'ubuntu'` not `ubuntu`.

## EC2 tagging requirements

Tag instances in AWS Console or Terraform:

| Tag Key | Tag Value | Purpose |
|---------|-----------|---------|
| Environment | ansible-lab | Matches filter |
| Role | webservers or appservers | Creates keyed group |

Verify tags:

```bash
aws ec2 describe-instances \
  --filters "Name=tag:Environment,Values=ansible-lab" \
  --query 'Reservations[].Instances[].{Id:InstanceId,Role:Tags[?Key==`Role`].Value|[0],IP:PrivateIpAddress,State:State.Name}' \
  --output table \
  --profile lab-terraform
```

## Verifying dynamic inventory

### Graph view

```bash
cd ~/terraform-ansible-labs/ansible/extended/labs
export AWS_PROFILE=lab-terraform

ansible-inventory -i inventory/aws_ec2.yml --graph
```

Expected:

```text
@role_webservers:
  |--10.0.1.10
  |--10.0.1.11
@role_appservers:
  |--10.0.1.12
@aws_region_us_east_1:
  |--10.0.1.10
  |--10.0.1.11
  |--10.0.1.12
```

### JSON inspection

```bash
ansible-inventory -i inventory/aws_ec2.yml --list | python3 -m json.tool | head -60
```

Check `_meta.hostvars` for `ansible_host`, `ansible_user`, tags.

### Host-specific variables

```bash
ansible-inventory -i inventory/aws_ec2.yml --host 10.0.1.10
```

### Connectivity

```bash
ansible -i inventory/aws_ec2.yml role_webservers -m ansible.builtin.ping
```

## Running playbooks

```bash
# All instances in web role group
ansible-playbook -i inventory/aws_ec2.yml playbooks/loops-packages.yml \
  --limit role_webservers

# Single instance by IP (as shown in inventory)
ansible-playbook -i inventory/aws_ec2.yml playbooks/handlers-nginx.yml \
  --limit 10.0.1.10
```

## Inventory refresh behavior

Every Ansible invocation re-queries EC2 unless inventory caching is configured. After ASG replacement:

```bash
# Before: 2 web instances
ansible-inventory -i inventory/aws_ec2.yml --graph

# Terminate one, launch replacement, then:
ansible-inventory -i inventory/aws_ec2.yml --graph
# New IP appears without editing files
```

## Directory inventory pattern

Production teams often use:

```
inventory/
  aws/
    aws_ec2.yml
  group_vars/
    role_webservers.yml
    all.yml
```

Ansible merges `group_vars` beside the inventory source when using directory layout.

## Combining static and dynamic

Multiple inventory sources:

```bash
ansible -i inventory/hosts.ini -i inventory/aws_ec2.yml all -m ping
```

Later sources override earlier for duplicate hosts. Use carefully to avoid conflicts.

## Troubleshooting

### Empty inventory

| Check | Command |
|-------|---------|
| Credentials | `aws sts get-caller-identity` |
| Region | Match `regions:` in plugin and `AWS_DEFAULT_REGION` |
| Tags | Verify Environment=ansible-lab on instances |
| State | Stopped instances filtered out |
| Filters | Temporarily remove filters to test |

```bash
# Debug plugin
ansible-inventory -i inventory/aws_ec2.yml --list -vvv 2>&1 | tail -30
```

### Auth errors

```
Unable to locate credentials
```

Fix: `export AWS_PROFILE=lab-terraform` or configure `~/.aws/credentials`

### Plugin not found

```
Failed to parse inventory with 'amazon.aws.aws_ec2' plugin
```

Fix: `ansible-galaxy collection install amazon.aws`

### UNREACHABLE after inventory succeeds

Inventory works but SSH fails:

- Control node not in VPC — use bastion or VPN
- Wrong `ansible_user` in compose
- Security group blocks port 22

### Wrong group membership

- Check `tags.Role` spelling (case-sensitive)
- Verify `keyed_groups` key path: `tags.Role` not `tag.Role`
- Inspect: `ansible-inventory --host <ip>`

## Fallback without AWS

If AWS is unavailable, continue labs with static inventory:

```bash
ansible-inventory -i inventory/hosts.ini --graph
ansible-playbook -i inventory/hosts.ini playbooks/site.yml
```

Compare `hosts.ini` groups to what `keyed_groups` would produce from tags.

## Security best practices

1. **Least-privilege IAM** — only `ec2:DescribeInstances` for inventory read role
2. **No long-lived keys on shared CI** — use OIDC or instance roles
3. **Filter aggressively** — tag filters prevent touching production instances
4. **Private IPs** — avoid exposing public IPs in compose when bastion used
5. **Audit inventory** — log `--graph` output in CI before destructive plays

## Plugin documentation

```bash
ansible-doc -t inventory amazon.aws.aws_ec2
```

## Related resources

- [Static Inventory](static-inventory.md)
- [Lab 07 — Dynamic Inventory](../../labmanuals/lab07-dynamic-inventory.md)
- [dynamic-inventory.html](../../html/dynamic-inventory.html) — interactive architecture
- `labs/dynamic_inventory/README.md`

## Quick reference

```bash
export AWS_PROFILE=lab-terraform
ansible-galaxy collection install amazon.aws
ansible-inventory -i inventory/aws_ec2.yml --graph
ansible -i inventory/aws_ec2.yml role_webservers -m ansible.builtin.ping
ansible-playbook -i inventory/aws_ec2.yml playbooks/loops-packages.yml
```

## Summary

The `amazon.aws.aws_ec2` inventory plugin queries EC2 at runtime, filters instances by tags and state, creates groups via `keyed_groups`, and sets connection variables through `compose`. Install boto3 and the amazon.aws collection, tag instances consistently, verify with `ansible-inventory --graph`, and run playbooks with `-i inventory/aws_ec2.yml`.

---

*Ansible Extended Track · Lesson 6 AP-03 · Curriculum v2*
