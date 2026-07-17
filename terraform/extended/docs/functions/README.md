# Functions, expressions, and collections

Terraform functions transform values; they do not create infrastructure. Use collection functions such as `toset`, `sort`, and `merge` to normalize stable inputs. Use string functions to create predictable names and `cidrsubnet` to derive non-overlapping networks.

Prefer `for_each` with stable map keys for resources whose instances should survive collection reordering. Use `count` only where an ordinal identity is meaningful. Validate complex variable shapes with explicit object types and variable validation rules.

Evaluate expressions in `terraform console` before deploying. Keep locals focused on transformations that improve readability.
