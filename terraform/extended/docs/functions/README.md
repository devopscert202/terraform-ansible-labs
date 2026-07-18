# Terraform Functions, for_each, and Dynamic Blocks

## Objective (conceptual)

HCL **functions** transform values at plan time—strings, collections, CIDR math, encoding. **`for_each`** creates one resource per map or set element instead of copy-pasting blocks. **Dynamic blocks** generate nested blocks (like security group rules) from data structures.

The mental model: functions are **spreadsheet formulas** for infrastructure; `for_each` is **iterate a collection**; dynamic blocks are **generate repeated nested stanzas** from a variable.

**Interactive reference:** [Functions](../../html/functions.html)

## Built-in functions (Lab 13)

```hcl
variable "application" {
  type    = string
  default = "payments api"
}

variable "cidrs" {
  type    = list(string)
  default = ["10.0.2.0/24", "10.0.1.0/24", "10.0.1.0/24"]
}

locals {
  slug          = lower(replace(var.application, " ", "-"))
  unique_cidrs  = sort(tolist(toset(var.cidrs)))
  subnet_prefix = cidrsubnet("10.20.0.0/16", 8, 12)
  configuration = jsonencode({ name = local.slug, cidrs = local.unique_cidrs })
}
```

| Function | Role in lab |
|----------|-------------|
| `replace`, `lower` | Build DNS-safe slug from app name |
| `toset`, `tolist`, `sort` | Deduplicate and order CIDR list |
| `cidrsubnet` | Calculate subnet from parent CIDR |
| `jsonencode` | Serialize map for output or APIs |

Use `terraform console` to experiment: `cidrsubnet("10.0.0.0/16", 8, 1)`.

## for_each with collections (Lab 12)

```hcl
variable "subnets" {
  type = map(object({ cidr = string, az = string }))
  default = {
    app_a = { cidr = "10.0.1.0/24", az = "us-east-1a" }
    app_b = { cidr = "10.0.2.0/24", az = "us-east-1b" }
  }
}

resource "terraform_data" "subnet" {
  for_each = var.subnets
  input    = { name = each.key, cidr = each.value.cidr, az = each.value.az }
}

output "subnet_ids" {
  value = { for name, item in terraform_data.subnet : name => item.id }
}
```

- `each.key` — map key (`app_a`)
- `each.value` — map value object
- Address: `terraform_data.subnet["app_a"]`

## Dynamic ingress blocks (Lab 14)

```hcl
variable "ingress_rules" {
  type = map(object({
    port          = number
    cidr_blocks   = list(string)
    description   = string
  }))
  default = {
    https = { port = 443, cidr_blocks = ["10.0.0.0/8"], description = "internal HTTPS" }
    http  = { port = 80, cidr_blocks = ["10.0.0.0/8"], description = "internal HTTP" }
  }
}

resource "aws_security_group" "service" {
  name_prefix = "extended-dynamic-"
  description = "Dynamic ingress demonstration"

  dynamic "ingress" {
    for_each = var.ingress_rules
    content {
      description = ingress.value.description
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = "tcp"
      cidr_blocks = ingress.value.cidr_blocks
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

Adding a map entry adds an `ingress` stanza without editing HCL structure.

## count vs for_each (when to choose)

| | `count` | `for_each` |
|---|---------|------------|
| Index | Integer `count.index` | Stable map/set keys |
| Address | `resource.name[0]` | `resource.name["key"]` |
| Destroy one | Shifts indices—risky | Stable keys—preferred |

Prefer `for_each` for named infrastructure.

## Function categories (reference)

- **String:** `join`, `split`, `trim`, `format`
- **Collection:** `merge`, `keys`, `values`, `lookup`
- **Numeric:** `min`, `max`, `parseint`
- **CIDR:** `cidrhost`, `cidrsubnet`, `cidrcontains`
- **Encoding:** `jsonencode`, `jsondecode`, `base64encode`

## Operational commands (reference)

```bash
cd terraform/extended/labs/lab13-functions
terraform console
# try: lower("Hello World")

cd ../lab12-collections
terraform plan

cd ../lab14-dynamic-blocks
terraform plan -var='ingress_rules={ssh={port=22,cidr_blocks=["203.0.113.0/32"],description="admin"}}'
```

---

## Hands-On Labs

| Lab | Description |
|-----|-------------|
| [Lab 12: Collections](../../labmanuals/lab12-collections.md) | `for_each` over maps, set functions |
| [Lab 13: Functions](../../labmanuals/lab13-functions.md) | String, collection, CIDR, JSON functions |
| [Lab 14: Dynamic Blocks](../../labmanuals/lab14-dynamic-blocks.md) | `dynamic` ingress rules from variables |
