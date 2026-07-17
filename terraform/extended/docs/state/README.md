# State and shared ownership

Terraform state maps configuration to real infrastructure. Keep it in a protected remote backend for team work, enable encryption and locking, and use least-privilege IAM. A backend block cannot use normal input variables, so backend settings belong in a reviewed `backend.hcl` file or CI configuration.

Use `terraform init -backend-config=backend.hcl`, review migration prompts, and run `terraform state list` only for diagnosis. Never edit state by hand. S3 native lockfiles (`use_lockfile = true`) prevent concurrent writes; use a unique key per environment and component.

State can contain sensitive values even when CLI output is redacted. Restrict bucket access, enable versioning, and avoid publishing state files.
