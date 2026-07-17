# Terraform Extended Lab Manuals

Fifteen validation-first labs for Terraform 1.5+. AWS examples require an authenticated `AWS_PROFILE` or IAM role; Terraform source never contains access keys. Backend labs assume an approved, pre-created S3 bucket only when you initialize the real backend.

| Lab | Focus | Lab directory |
|---|---|---|
| 01 | [Console VPC](lab01-console-vpc.md) | `lab01-console-vpc` |
| 02 | [Validate-only](lab02-validate-only.md) | `lab02-validate-only` |
| 03 | [Multi-cloud providers](lab03-multi-cloud-providers.md) | `lab03-multi-cloud-providers` |
| 04 | [local-exec provisioner](lab04-local-exec-provisioner.md) | `lab04-local-exec-provisioner` |
| 05 | [remote-exec provisioner](lab05-remote-exec-provisioner.md) | `lab05-remote-exec-provisioner` |
| 06 | [Workspaces](lab06-workspaces.md) | `lab06-workspaces` |
| 07 | [S3 backend](lab07-s3-backend.md) | `lab07-s3-backend` |
| 08 | [State keys](lab08-state-keys.md) | `lab08-state-keys` |
| 09 | [State locking](lab09-state-locking.md) | `lab09-state-locking` |
| 10 | [State migration](lab10-state-migration.md) | `lab10-state-migration` |
| 11 | [Remote state consumer](lab11-remote-state-consumer.md) | `lab11-remote-state-consumer` |
| 12 | [Collections](lab12-collections.md) | `lab12-collections` |
| 13 | [Functions](lab13-functions.md) | `lab13-functions` |
| 14 | [Dynamic blocks](lab14-dynamic-blocks.md) | `lab14-dynamic-blocks` |
| 15 | [Capstone projects](lab15-capstone-projects.md) | `lab15-capstone-projects` |

## Working agreement

Run commands from the corresponding directory under `../labs/`. Run `terraform fmt -recursive`, initialization, and validation before reviewing a plan. Do not commit `.terraform/`, state files, private `*.tfvars`, private keys, or generated plans. Destroy training infrastructure after evidence is captured.
