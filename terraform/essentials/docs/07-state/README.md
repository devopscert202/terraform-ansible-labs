# 07 — State

## Overview

Terraform state is a JSON document that maps each resource in your configuration to its real-world identity. Without state, Terraform would not know that `aws_instance.web` in your `.tf` file corresponds to `i-0abc123` in AWS. State also caches attributes for planning and tracks metadata like dependencies.

Lab 06 uses **local state** (default `terraform.tfstate` file). Production teams use **remote backends** with locking. This chapter teaches inspection, drift, and safe handling — beginners who treat state casually often cause orphan resources or data loss.

### Why this matters for beginners

Deleting `terraform.tfstate` while EC2 instances still run leaves **unmanaged** resources that continue billing. Committing state to a public git repo may expose **sensitive values**. Understanding state is as important as understanding HCL.

---

## Key concepts

| Concept | Description |
|---------|-------------|
| `terraform.tfstate` | Default local state file |
| Resource address | Key in state: `random_pet.first` |
| Serial | Incremented on each state write |
| Lineage | UUID for state history |
| Refresh | Update state from live APIs during plan |
| Drift | Real infra differs from config |
| Backend | Where state is stored (local, S3, etc.) |
| State locking | Prevents concurrent applies |

---

## State mapping diagram

```
 Configuration                    State                         Cloud
┌──────────────────┐         ┌──────────────────┐         ┌─────────────┐
│ random_pet.first │ ◀─────▶ │ "name": "first"  │ ◀─────▶ │ (provider)  │
│ prefix, length   │         │ "id": "state-lab │         │ random pet  │
└──────────────────┘         │  -valid-moth"    │         └─────────────┘
                             └──────────────────┘
```

---

## Lab 06 configuration

`labs/lab06-local-state/main.tf`:

```hcl
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# No backend block means Terraform uses local terraform.tfstate.
resource "random_pet" "first" {
  prefix = "state-lab"
  length = 2
}

output "first_resource" {
  value = random_pet.first.id
}
```

---

## Step-by-step inspection

```bash
cd terraform/essentials/labs/lab06-local-state
terraform init
terraform apply
```

Note output like `first_resource = "state-lab-valid-moth"`.

### List resources in state

```bash
terraform state list
```

Expected:

```
random_pet.first
```

### Show one resource

```bash
terraform state show random_pet.first
```

Expected attributes include `id`, `length = 2`, `prefix = "state-lab"`.

### Pull raw JSON

```bash
terraform state pull | head -20
```

Shows `version`, `serial`, `lineage`, `resources` array.

### Destroy

```bash
terraform destroy
```

---

## State file structure (simplified)

```json
{
  "version": 4,
  "terraform_version": "1.5.0",
  "serial": 1,
  "lineage": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "outputs": {
    "first_resource": {
      "value": "state-lab-valid-moth",
      "type": "string"
    }
  },
  "resources": [
    {
      "mode": "managed",
      "type": "random_pet",
      "name": "first",
      "provider": "provider[\"registry.terraform.io/hashicorp/random\"]",
      "instances": [
        {
          "attributes": {
            "id": "state-lab-valid-moth",
            "length": 2,
            "prefix": "state-lab"
          }
        }
      ]
    }
  ]
}
```

---

## State subcommands

| Command | Purpose |
|---------|---------|
| `terraform state list` | All resource addresses |
| `terraform state show ADDR` | One resource detail |
| `terraform state pull` | Print state JSON to stdout |
| `terraform state push` | Upload state (dangerous) |
| `terraform state rm ADDR` | Remove from state without destroy |
| `terraform state mv SRC DST` | Rename address in state |

### state rm warning

```bash
terraform state rm random_pet.first
```

Terraform **stops managing** the resource. The random pet (or EC2 instance) may still exist but Terraform forgets it.

### state mv for refactoring

```bash
terraform state mv random_pet.first random_pet.primary
```

Updates state only — no cloud API calls.

---

## Drift detection

```
1. Engineer changes EC2 tag in AWS Console
2. terraform plan refreshes state from API
3. Plan shows: ~ tags (configuration differs)
4. terraform apply reconciles back to .tf
```

---

## Local vs remote backend

| Feature | Local (Lab 06) | Remote (S3 + DynamoDB) |
|---------|----------------|------------------------|
| Storage | `terraform.tfstate` on disk | S3 bucket |
| Locking | None | DynamoDB table |
| Team use | Solo labs only | Production standard |
| Encryption | Your responsibility | SSE-KMS on bucket |

### Remote backend example (reference)

```hcl
terraform {
  backend "s3" {
    bucket         = "my-org-terraform-state"
    key            = "essentials/lab06/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
```

Migrate with:

```bash
terraform init -migrate-state
```

---

## .gitignore recommendations

```
.terraform/
*.tfstate
*.tfstate.*
.terraform.tfstate.backup
terraform.tfvars
```

**Do commit:** `.terraform.lock.hcl`

---

## Common mistakes

| Mistake | Impact | Fix |
|---------|--------|-----|
| Commit tfstate to git | Secrets exposed; merge conflicts | .gitignore state files |
| Manual JSON edits | Corrupt state | Use state subcommands |
| Concurrent apply (no lock) | Corrupted state | Remote backend + locking |
| Delete state with resources running | Orphans | destroy first, then delete state |
| `state rm` thinking it deletes cloud | Orphan resources | Use `terraform destroy` |
| Assuming sensitive not in state | Leak via state file | Encrypt backend |

---

## Links

| Resource | Path |
|----------|------|
| Lab 06 | [labmanuals/lab06-local-state.md](../../labmanuals/lab06-local-state.md) |
| HTML: State | [html/state.html](../../html/state.html) |
| Previous | [06-variables/README.md](../06-variables/README.md) |
| Next | [08-modules/README.md](../08-modules/README.md) |

---

## Hands-on lab

**[Lab 06 — Local State](../../labmanuals/lab06-local-state.md)** — No AWS required.

---

## Key takeaways

1. State links **configuration addresses** to **real resource IDs**.
2. **Never commit** state files; they may contain sensitive data.
3. Use `state list` and `state show` to inspect without opening JSON manually.
4. **Drift** is detected during plan refresh.
5. Teams need **remote backends with locking**.

---

## Next steps

Read [08 — Modules](../08-modules/README.md) for reusable infrastructure composition.
