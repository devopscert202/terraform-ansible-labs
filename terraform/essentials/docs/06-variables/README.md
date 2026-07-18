# Terraform Variables and Locals

## Objective (conceptual)

**Input variables** parameterize a module so the same code targets different environments. **Locals** compute derived values once and reuse them across resources—keeping tags and names DRY without exposing another input. **tfvars** files supply values per environment; CLI `-var` flags override at runtime.

The mental model: variables are the **knobs** operators turn; locals are **private helpers** inside the module; defaults document safe training values while production passes explicit tfvars in CI.

**Interactive reference:** [Variables and tfvars](../../html/variables.html)

## Variable declaration (Lab 05)

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

## Locals merge tags onto resources

```hcl
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

`merge` combines maps; later keys win on collision. Every resource sharing `local.common_tags` updates together when `var.tags` changes.

## Value precedence (highest wins)

1. `-var` / `-var-file` on CLI
2. `*.auto.tfvars` (alphabetical)
3. `terraform.tfvars`
4. Environment variables `TF_VAR_name`
5. `default` in `variable` block

Lab 08 demonstrates tfvars for non-secret and sensitive values separately.

## tfvars example pattern

Copy `terraform.tfvars.example` to `terraform.tfvars` locally—commit the example, gitignore the real file if it holds environment-specific data.

## Validation and types (essentials scope)

- `type = string | number | bool | list(...) | map(...)` catches category errors at plan time.
- `description` documents intent for module consumers.
- `sensitive = true` on variables redacts values in logs (Lab 08).

## Lab 08: configuration map

```hcl
locals {
  configuration = {
    cloud        = var.cloud
    department   = var.department
    cost_code    = var.cost_code
    ip_address   = var.ip_address
    phone_number = var.phone_number
  }
}

output "phone_number" {
  description = "Sensitive values are redacted in normal CLI output but remain in state."
  value       = local.configuration.phone_number
  sensitive   = true
}
```

Never commit real phone numbers or secrets—use placeholders in examples.

## Variables vs outputs vs locals

| Construct | Direction | Typical use |
|-----------|-----------|-------------|
| `variable` | In | Region, instance size, feature flags |
| `output` | Out | IDs, ARNs for humans or remote state consumers |
| `locals` | Internal | Computed names, merged tags, repeated expressions |

## Operational commands (reference)

```bash
cd terraform/essentials/labs/lab05-variables
terraform init
terraform plan -var="server_name=demo-web"
terraform apply -var-file=terraform.tfvars

cd ../lab08-tfvars-secrets
terraform plan
terraform output phone_number
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 05: Variables](../../labmanuals/lab05-variables.md) | Input variables, locals, merged tags on EC2 |
| [Lab 08: tfvars and Secrets](../../labmanuals/lab08-tfvars-secrets.md) | tfvars files, sensitive variables and outputs |
