# 06 — Variables

## Overview

Variables parameterize Terraform configurations so one codebase deploys multiple environments. Instead of copying `main.tf` for dev and prod, you change **inputs** — via defaults, `terraform.tfvars`, or environment variables — while keeping resource logic identical.

This chapter covers Lab 05 (typed variables, locals, tag merge) and previews Lab 08 (validation, secrets). Variables are the primary interface between platform teams and application teams consuming modules.

### Why this matters for beginners

Hard-coding `instance_type = "t3.micro"` works once. When you need `t3.large` in staging, variables prevent a search-and-replace across dozens of files. **Type constraints** catch `instance_type = 123` at validate time instead of at the AWS API.

---

## Key concepts

| Concept | Scope | Set by caller? |
|---------|-------|----------------|
| `variable` | Input from outside | Yes |
| `locals` | Internal computed | No |
| `output` | Exported result | N/A |
| `default` | Fallback value | In variable block |
| `terraform.tfvars` | Auto-loaded values file | Yes |
| `TF_VAR_*` | Environment injection | Yes |
| `validation` | Input rules | In variable block |

---

## Variable precedence (highest wins)

```
1. -var and -var-file on CLI
2. *.auto.tfvars (alphabetical)
3. terraform.tfvars
4. TF_VAR_<name> environment variables
5. default in variable block
```

---

## Lab 05 — Full example

### variables.tf

```hcl
variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "server_name" {
  type        = string
  description = "Name for the web server."
  default     = "variables-lab-web"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "tags" {
  type = map(string)
  default = {
    Environment = "training"
    Owner       = "platform-team"
  }
}
```

### main.tf (locals + resource)

```hcl
provider "aws" {
  region = var.aws_region
}

locals {
  common_tags = merge(var.tags, {
    Name      = var.server_name
    Service   = "terraform-essentials"
    ManagedBy = "Terraform"
  })
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  tags          = local.common_tags
}
```

### outputs.tf

```hcl
output "instance_id" {
  value = aws_instance.web.id
}

output "public_ip" {
  value = aws_instance.web.public_ip
}
```

---

## Passing values

### Defaults only

```bash
terraform plan
# Uses all defaults from variables.tf
```

### terraform.tfvars

Create `terraform.tfvars` (gitignore if environment-specific):

```hcl
aws_region    = "us-east-1"
server_name   = "my-custom-web"
instance_type = "t3.micro"

tags = {
  Environment = "training"
  Owner       = "platform-team"
}
```

### CLI override

```bash
terraform plan -var="instance_type=t3.small"
```

### Environment variable

```bash
export TF_VAR_server_name="from-env"
terraform plan
```

---

## Type reference

```hcl
variable "name"     { type = string }
variable "count"    { type = number }
variable "enabled"  { type = bool }
variable "azs"      { type = list(string) }
variable "tags"     { type = map(string) }

variable "config" {
  type = object({
    size = string
    port = number
  })
}
```

---

## locals vs variables

```hcl
# Variable — external input
variable "environment" {
  type    = string
  default = "dev"
}

# Local — derived inside module
locals {
  name_prefix = "${var.environment}-app"
  common_tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}
```

Use locals to avoid repeating expressions and to keep resource blocks readable.

---

## merge() for tags

```hcl
locals {
  common_tags = merge(var.tags, {
    Name = var.server_name
  })
}
```

Later map keys override earlier on collision.

---

## Lab 08 preview — validation

```hcl
variable "cloud" {
  type = string
  validation {
    condition     = contains(["aws", "azure", "gcp", "vmware"], var.cloud)
    error_message = "cloud must be aws, azure, gcp, or vmware."
  }
}
```

Validation runs during `plan` and `apply`, not during `validate` for all cases — but invalid values are rejected before API calls.

---

## Common mistakes

| Mistake | Result | Fix |
|---------|--------|-----|
| Untyped variables | Weak error messages | Add `type =` |
| Secrets in tfvars in git | Credential leak | TF_VAR_ or secret manager |
| Confusing locals with variables | Can't override from outside | Use variable for inputs |
| Wrong precedence assumption | Unexpected values | Check CLI > tfvars > TF_VAR > default |
| Missing description | Poor module docs | Add `description =` |
| `sensitive` thought to hide from state | Secret in plaintext state | Encrypt backend |

---

## Links

| Resource | Path |
|----------|------|
| Lab 05 | [labmanuals/lab05-variables.md](../../labmanuals/lab05-variables.md) |
| Lab 08 | [labmanuals/lab08-tfvars-secrets.md](../../labmanuals/lab08-tfvars-secrets.md) |
| HTML: Variables | [html/variables.html](../../html/variables.html) |
| Previous | [05-quality/README.md](../05-quality/README.md) |
| Next | [07-state/README.md](../07-state/README.md) |

---

## Hands-on labs

1. **[Lab 05](../../labmanuals/lab05-variables.md)** — EC2 with variables and merged tags.
2. **[Lab 08](../../labmanuals/lab08-tfvars-secrets.md)** — Validation and sensitive inputs.

---

## Key takeaways

1. **Variables** are inputs; **locals** are internal computations.
2. Know **precedence** when debugging unexpected values.
3. Use **types** and **validation** to fail fast.
4. **merge()** composes tag maps cleanly in Lab 05.
5. Never commit **secrets** in tfvars — use `TF_VAR_` or ignored files.

---

## Next steps

Read [07 — State](../07-state/README.md) for state file anatomy and inspection commands.
