# Lab 07: Implementing Dynamic Inventories

> **Goal:** Build inventory from live AWS EC2 data using the `amazon.aws.aws_ec2` plugin, keyed groups, and compose variables.
> **Time:** ~60 min · **Files:** `labs/inventory/aws_ec2.yml`, `labs/dynamic_inventory/README.md` · **Source:** Lesson 6 AP-03

## Before you start

- AWS credentials configured (`AWS_PROFILE=lab-terraform`)
- EC2 instances tagged `Environment=ansible-lab` and `Role=webservers` or `Role=appservers`
- [AWS lab setup](../../../curriculum/setup/aws-lab-environment.md) — add tags to instances
- Control node: `pip install boto3` and `ansible-galaxy collection install amazon.aws`

## Architecture

```
ansible-inventory  -->  AWS EC2 API  -->  keyed_groups (role_webservers, ...)
                              |
                         filters: running + tag Environment
```

Static inventory (`hosts.ini`) is fine for fixed labs. Dynamic inventory scales when instances are created/destroyed by Terraform or Auto Scaling.

---

## Steps

### Step 1 — Install collection and dependencies

```bash
cd ~/terraform-ansible-labs/ansible/extended/labs
ansible-galaxy collection install amazon.aws
python3 -c "import boto3; print(boto3.__version__)"
export AWS_PROFILE=lab-terraform
export AWS_DEFAULT_REGION=us-east-1
```

**Validate**

```text
1.x.x
```

No import error for boto3.

---

### Step 2 — Review plugin configuration

```bash
cat inventory/aws_ec2.yml
```

Key settings:

| Key | Purpose |
|-----|---------|
| `plugin: amazon.aws.aws_ec2` | Inventory plugin FQCN |
| `filters` | Only running instances with tag |
| `keyed_groups` | Create `role_webservers` from `Role` tag |
| `compose` | Set `ansible_host` to private IP |

**Validate**

File is valid YAML (no tabs).

---

### Step 3 — Tag EC2 instances in AWS Console

For each lab instance:

| Tag key | Value |
|---------|-------|
| Environment | ansible-lab |
| Role | webservers (or appservers) |

**Validate**

```bash
aws ec2 describe-instances --filters "Name=tag:Environment,Values=ansible-lab"   --query 'Reservations[].Instances[].{Id:InstanceId,Role:Tags[?Key==`Role`].Value|[0],IP:PrivateIpAddress}'   --output table --profile lab-terraform
```

At least one instance listed.

---

### Step 4 — List dynamic inventory (graph)

```bash
ansible-inventory -i inventory/aws_ec2.yml --graph
```

**Validate**

```text
@role_webservers:
  |--i-0abc...
@aws_region_us_east_1:
  |--i-0abc...
```

Hostnames may be instance IDs or IPs depending on plugin config.

---

### Step 5 — JSON inventory inspect

```bash
ansible-inventory -i inventory/aws_ec2.yml --list | head -40
```

**Validate**

JSON includes `_meta.hostvars` with `ansible_host` set to private IP.

---

### Step 6 — Ping via dynamic inventory

Ensure SSH from control node to instance private IPs works (same VPC).

```bash
ansible -i inventory/aws_ec2.yml role_webservers -m ansible.builtin.ping
```

**Validate**

```text
i-... | SUCCESS => { "ping": "pong" }
```

---

### Step 7 — Combine with static vars (optional pattern)

Create `inventory/aws/` directory pattern:

```bash
mkdir -p inventory/aws
cp inventory/aws_ec2.yml inventory/aws/
```

Document in notes: some teams place `group_vars/` beside inventory source.

**Validate**

Directory exists for future expansion.

---

### Step 8 — Run a playbook against dynamic group

```bash
ansible-playbook -i inventory/aws_ec2.yml playbooks/loops-packages.yml --limit role_webservers
```

**Validate**

Play targets EC2 instances in `role_webservers` group only.

---

### Step 9 — Refresh after instance change

Launch or terminate a tagged instance, then:

```bash
ansible-inventory -i inventory/aws_ec2.yml --graph
```

**Validate**

Host list reflects current AWS state (no manual inventory edit).

---

### Step 10 — Troubleshooting checklist

| Check | Command |
|-------|---------|
| Credentials | `aws sts get-caller-identity --profile lab-terraform` |
| Region | `echo $AWS_DEFAULT_REGION` |
| Plugin | `ansible-doc -t inventory amazon.aws.aws_ec2` |
| SSH | `ssh ubuntu@<private-ip>` |

**Validate**

All four checks pass before lab sign-off.

---

## Fallback: local mock (no AWS)

If AWS is unavailable, continue using `inventory/hosts.ini` and compare structure to `aws_ec2.yml` — document what each plugin key would map to.

---

## Done when

- [ ] `amazon.aws` collection installed
- [ ] Instances tagged `Environment=ansible-lab`
- [ ] `--graph` shows keyed groups
- [ ] `ansible.builtin.ping` succeeds via dynamic inventory
- [ ] You can explain filters vs keyed_groups

## If something fails

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Empty inventory | Wrong tags/region | Verify filters match your tags |
| Auth error | Missing profile | `export AWS_PROFILE=...` |
| UNREACHABLE | SSH to private IP | Run ansible from control node in VPC |
| Plugin not found | Collection missing | `ansible-galaxy collection install amazon.aws` |

## Cleanup

Remove test tags or stop instances per AWS setup guide. No files to delete in repo.

---
*Source: Lesson 6 AP-03 · Next: [lab08](lab08-roles-project.md) · Deep dive: [dynamic inventory AWS](../docs/inventory/dynamic-inventory-aws.md)*
