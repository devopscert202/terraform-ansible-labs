# Dynamic Inventory on AWS

The `amazon.aws.aws_ec2` plugin builds inventory from live EC2 API data.

## Plugin config

```yaml
plugin: amazon.aws.aws_ec2
regions:
  - us-east-1
filters:
  instance-state-name: running
  tag:Environment: ansible-lab
keyed_groups:
  - key: tags.Role
    prefix: role
```

## Prerequisites

```bash
pip install boto3
ansible-galaxy collection install amazon.aws
export AWS_PROFILE=lab-terraform
```

## Test

```bash
ansible-inventory -i inventory/aws_ec2.yml --graph
```

## Related lab

[lab07 — Dynamic inventory](../../labmanuals/lab07-dynamic-inventory.md)
