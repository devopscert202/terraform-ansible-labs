# Dynamic inventory notes

The `inventory/aws_ec2.yml` file uses the **amazon.aws.aws_ec2** inventory plugin.

## Prerequisites

```bash
sudo apt install -y python3-boto3
ansible-galaxy collection install amazon.aws
export AWS_PROFILE=lab-terraform
export AWS_DEFAULT_REGION=us-east-1
```

## Tag your EC2 instances

| Tag key | Example value |
|---------|---------------|
| Environment | ansible-lab |
| Role | webservers |

## Test

```bash
ansible-inventory -i inventory/aws_ec2.yml --graph
ansible -i inventory/aws_ec2.yml role_webservers -m ansible.builtin.ping
```
