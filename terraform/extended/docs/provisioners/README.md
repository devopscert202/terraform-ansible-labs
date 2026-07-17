# Provisioners

Provisioners are an escape hatch, not a configuration-management replacement. Prefer cloud-init, image builds, or a dedicated tool such as Ansible. Use `local-exec` only for an action coupled to Terraform lifecycle and ensure it is idempotent.

`remote-exec` requires network reachability and secure authentication. Keep SSH private-key paths in a local ignored tfvars file or environment variable; never place the key itself in Terraform code. A failed provisioner taints or fails its parent resource according to its settings, so test the command outside Terraform first.

Destroy provisioners are particularly risky because dependencies may already be disappearing. Keep cleanup logic explicit and observable.
