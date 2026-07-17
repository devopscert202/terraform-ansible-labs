# AWS Lab Environment Setup

Provision this environment **before** the 10-hour Ansible or Terraform blocks. Budget ~30 minutes once; reuse for all labs.

## Architecture

| Node | Role | Spec |
|------|------|------|
| `control` | Ansible control / Terraform workstation | Ubuntu 22.04, t3.small, us-east-1 |
| `web1`, `web2` | Ansible managed targets | Ubuntu 22.04, t3.micro, us-east-1 |

All nodes in one VPC security group:

- SSH (22) from your IP
- For Terraform EC2 labs: allow HTTP (80) from your IP on practice instances

## Create EC2 instances

1. Region: **us-east-1**
2. AMI: **Ubuntu 22.04 LTS**
3. Key pair: create or reuse `lab-key.pem` (`chmod 400 lab-key.pem`)
4. Launch 3 instances with the security group above
5. Note private IPs (for Ansible inventory) and public IPs (for SSH)

## Configure the control node

```bash
ssh -i lab-key.pem ubuntu@<control-public-ip>
sudo apt update && sudo apt install -y ansible python3-pip unzip
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install -y terraform
terraform version
ansible --version
```

## SSH from control to targets

On the control node:

```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519
ssh-copy-id -i ~/.ssh/id_ed25519.pub ubuntu@<web1-private-ip>
ssh-copy-id -i ~/.ssh/id_ed25519.pub ubuntu@<web2-private-ip>
ssh ubuntu@<web1-private-ip> hostname
```

## AWS credentials for Terraform

Use a named profile — do not embed keys in `.tf` files.

```bash
aws configure --profile lab-terraform
# or on EC2: attach an IAM role with EC2/VPC/S3/DynamoDB permissions for extended labs
export AWS_PROFILE=lab-terraform
export AWS_DEFAULT_REGION=us-east-1
```

## Clone course repo on control node

```bash
git clone <this-repo-url> ~/terraform-ansible-labs
cd ~/terraform-ansible-labs
```

## Validate

```bash
cd ~/terraform-ansible-labs/ansible/essentials/labs
ansible -i inventory/hosts.ini all -m ansible.builtin.ping
```

Expected: `pong` on each host.

## Teardown

Stop or terminate EC2 instances when finished. Run `terraform destroy` in any lab directory that created AWS resources.
