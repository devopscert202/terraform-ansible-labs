# Terraform Resources and Data Sources

## Objective (conceptual)

A **resource** is something Terraform owns: it knows the real ID, tracks attributes in state, and will create, update, or destroy the object to match your configuration. A **data source** is a read-only query—it never appears as a managed object in state, but its attributes can feed resource arguments.

The mental model: resources are **verbs with memory** (Terraform remembers them); data sources are **lookups** (Terraform asks the API once per plan/apply). Lab 02 combines both—lookup an AMI, then create an instance and security group that reference it.

**Interactive reference:** [Foundations](../../html/foundations.html)

## Resource addressing

- Syntax: `resource "TYPE" "NAME" { ... }`
- Reference: `aws_instance.web.id`, `aws_security_group.web.id`
- Dependencies: implicit when one resource references another; Terraform orders creates and destroys safely.

## Lab 02: EC2 stack

```hcl
resource "aws_security_group" "web" {
  name        = "${var.instance_name}-sg"
  description = "Lab 02 SSH access"

  ingress {
    description = "SSH from learner IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name      = "${var.instance_name}-sg"
    ManagedBy = "Terraform"
    Lab       = "terraform-essentials-lab02"
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.web.id]

  tags = {
    Name      = var.instance_name
    ManagedBy = "Terraform"
    Lab       = "terraform-essentials-lab02"
  }
}
```

- Security group must exist before the instance attaches it—Terraform infers that edge.
- `tags` propagate to the AWS console for cost and ownership tracking.

## Lab 03: resource without a cloud API

`random_string` demonstrates lifecycle commands without AWS cost:

```hcl
resource "random_string" "example" {
  length  = 12
  special = false
  upper   = false
}

output "generated_value" {
  value = random_string.example.result
}
```

Replacing this resource (change `length`) forces destroy-and-recreate in the plan.

## Data source behavior

- Evaluated during plan/apply; result may change if the cloud changes (new AMI published).
- Use when the ID is dynamic or owned outside this configuration.
- Prefix references with `data.` — e.g. `data.aws_ami.ubuntu.id`.

## Outputs expose resource attributes

```hcl
output "instance_arn" {
  value = aws_instance.web.arn
}
```

Outputs are for operators and downstream modules—not required for Terraform to manage resources.

## Tags and naming

Consistent `tags` (`ManagedBy`, `Lab`, `Name`) make console filtering and `destroy` verification easier. Interpolate `var.instance_name` so one variable renames every related object.

## Common mistakes

| Mistake | Fix |
|---------|-----|
| Hard-coded AMI per region | Use `data.aws_ami` with filters |
| `0.0.0.0/0` SSH in production | Restrict `var.ssh_cidr` to your IP |
| Editing resources in console only | Changes cause **drift** on next plan |
| Wrong resource type string | Run `terraform providers schema` or check registry docs |

## Operational commands (reference)

```bash
cd terraform/essentials/labs/lab02-ec2
terraform plan
terraform apply
terraform state list
terraform state show aws_instance.web
terraform destroy
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 02: EC2 Instance](../../labmanuals/lab02-ec2.md) | Security group, instance, AMI data source |
| [Lab 03: Plan, Apply, Destroy](../../labmanuals/lab03-plan-apply-destroy.md) | Random resource lifecycle, outputs, teardown |
