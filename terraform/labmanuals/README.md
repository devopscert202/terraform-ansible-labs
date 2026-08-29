# Terraform Lab Manuals — Index

**22 labs, `lab00`–`lab21`, across three tiers.** Work through them in order; each lab assumes
the previous one is complete.

| | |
|---|---|
| **New to Terraform** | [`../html/terraform-101.html`](../html/terraform-101.html) — **read this first**, before lab00 |
| **New to AWS** | [`../html/aws-primer.html`](../html/aws-primer.html) — read this second |
| **Lab code** | [`../labs/`](../labs/) — one root module per lab |
| **Concept docs** | [`../docs/`](../docs/) — deep dives per tier |
| **Visual pages** | [`../html/index.html`](../html/index.html) — concept, example, line-by-line |

Terraform `>= 1.5.0`, AWS provider `~> 5.0`, region `us-east-1`, instance type `t3.micro`.

## Before lab00

Starting from zero, read both primers in this order — they answer different questions:

1. [Terraform 101](../html/terraform-101.html) — what Terraform is, HCL and block anatomy,
   providers, every version-constraint operator, the CLI and plan symbols, state, and drift.
2. [AWS Primer](../html/aws-primer.html) — region, VPC, CIDR, subnet, internet gateway, route
   table, security group, EC2, key pair, IAM access keys, plus the `lab21` architecture diagram.

---

## Tier 1 — Basic (lab00–lab05)

Install, authenticate, declare a provider, create your first resource, and learn the
init / plan / apply / destroy loop.

| Lab | Title | Tier | Topic | Code |
|---|---|---|---|---|
| 00 | [AWS Setup and Init](lab00-aws-setup-and-init.md) | Basic | AWS credentials, provider block, first `init` | [`labs/lab00-aws-setup-and-init/`](../labs/lab00-aws-setup-and-init/) |
| 01 | [Providers and Init](lab01-providers-init.md) | Basic | `required_providers`, lock file, `validate` | [`labs/lab01-providers-init/`](../labs/lab01-providers-init/) |
| 02 | [Console VPC](lab02-console-vpc.md) | Basic | Manual console build, contrasted with IaC | [`labs/lab02-console-vpc/`](../labs/lab02-console-vpc/) (no `.tf`) |
| 03 | [First EC2 Instance](lab03-first-ec2.md) | Basic | AMI data source, security group, instance | [`labs/lab03-first-ec2/`](../labs/lab03-first-ec2/) |
| 04 | [Plan, Apply, Destroy](lab04-plan-apply-destroy.md) | Basic | The core workflow, no cloud cost | [`labs/lab04-plan-apply-destroy/`](../labs/lab04-plan-apply-destroy/) |
| 05 | [Format and Validate](lab05-fmt-validate.md) | Basic | `fmt`, `validate`, CI-style quality gates | [`labs/lab05-fmt-validate/`](../labs/lab05-fmt-validate/) |

Concepts: [`../html/basic.html`](../html/basic.html) · Docs: [`../docs/basic/`](../docs/basic/)

## Tier 2 — Intermediate (lab06–lab12)

Parameterise configuration, read state, extract modules, and generate resources from
collections.

| Lab | Title | Tier | Topic | Code |
|---|---|---|---|---|
| 06 | [Variables and Outputs](lab06-variables-outputs.md) | Intermediate | Typed inputs, locals, outputs | [`labs/lab06-variables-outputs/`](../labs/lab06-variables-outputs/) |
| 07 | [tfvars and Secrets](lab07-tfvars-secrets.md) | Intermediate | tfvars files, precedence, `sensitive` | [`labs/lab07-tfvars-secrets/`](../labs/lab07-tfvars-secrets/) |
| 08 | [Local State](lab08-local-state.md) | Intermediate | `terraform.tfstate`, refresh, drift | [`labs/lab08-local-state/`](../labs/lab08-local-state/) |
| 09 | [Modules](lab09-modules.md) | Intermediate | Child modules, inputs, outputs | [`labs/lab09-modules/`](../labs/lab09-modules/) |
| 10 | [Collections](lab10-collections.md) | Intermediate | `for_each` over maps and sets | [`labs/lab10-collections/`](../labs/lab10-collections/) |
| 11 | [Functions](lab11-functions.md) | Intermediate | String, collection, CIDR, encoding | [`labs/lab11-functions/`](../labs/lab11-functions/) |
| 12 | [Dynamic Blocks](lab12-dynamic-blocks.md) | Intermediate | Generated nested blocks from data | [`labs/lab12-dynamic-blocks/`](../labs/lab12-dynamic-blocks/) |

Concepts: [`../html/intermediate.html`](../html/intermediate.html) · Docs: [`../docs/intermediate/`](../docs/intermediate/)

## Tier 3 — Advanced (lab13–lab21)

Multiple providers, provisioners, workspaces, remote state with locking, migration, and the
end-to-end capstone.

| Lab | Title | Tier | Topic | Code |
|---|---|---|---|---|
| 13 | [Multiple Providers](lab13-multi-provider.md) | Advanced | Two providers, provider aliases | [`labs/lab13-multi-provider/`](../labs/lab13-multi-provider/) |
| 14 | [local-exec Provisioner](lab14-local-exec-provisioner.md) | Advanced | Run a command on the Terraform host | [`labs/lab14-local-exec-provisioner/`](../labs/lab14-local-exec-provisioner/) |
| 15 | [remote-exec Provisioner](lab15-remote-exec-provisioner.md) | Advanced | SSH `connection` block, inline commands | [`labs/lab15-remote-exec-provisioner/`](../labs/lab15-remote-exec-provisioner/) |
| 16 | [Workspaces](lab16-workspaces.md) | Advanced | `terraform.workspace`, per-env naming | [`labs/lab16-workspaces/`](../labs/lab16-workspaces/) |
| 17 | [S3 Backend](lab17-s3-backend.md) | Advanced | Remote state in S3, backend config files | [`labs/lab17-s3-backend/`](../labs/lab17-s3-backend/) |
| 18 | [State Keys and Locking](lab18-state-keys-locking.md) | Advanced | Key conventions, DynamoDB lock table | [`labs/lab18-state-keys-locking/`](../labs/lab18-state-keys-locking/) |
| 19 | [State Migration](lab19-state-migration.md) | Advanced | `init -migrate-state`, backups | [`labs/lab19-state-migration/`](../labs/lab19-state-migration/) |
| 20 | [Remote State Consumer](lab20-remote-state-consumer.md) | Advanced | `terraform_remote_state` data source | [`labs/lab20-remote-state-consumer/`](../labs/lab20-remote-state-consumer/) |
| 21 | [Capstone: VPC and EC2](lab21-capstone-vpc-ec2.md) | Advanced | VPC, IGW, subnet, route table, SG, EC2 | [`labs/lab21-capstone-vpc-ec2/`](../labs/lab21-capstone-vpc-ec2/) |

Concepts: [`../html/advanced.html`](../html/advanced.html) · Docs: [`../docs/advanced/`](../docs/advanced/)

---

## Totals

| Tier | Labs | Range |
|---|---|---|
| Basic | 6 | lab00–lab05 |
| Intermediate | 7 | lab06–lab12 |
| Advanced | 9 | lab13–lab21 |
| **Total** | **22** | **lab00–lab21** |

## Cost control

Each manual's **What you will build** table states the cost of every resource it creates. Any lab
that creates an EC2 instance, an S3 bucket, or a DynamoDB table bills while it runs — finish with
`terraform destroy` in that lab's directory. `lab00`, `lab01`, `lab04`, and `lab05` create nothing
billable, and `lab02` is console-only with no `.tf` files.
