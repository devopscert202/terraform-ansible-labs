# Terraform Concept Docs

Written deep dives, one directory per tier. Read the matching page in
[`../html/`](../html/index.html) first for the short version with a worked example, then come here
for the longer treatment, and do the lab in [`../labmanuals/`](../labmanuals/README.md).

These docs assume you already know what Terraform is. If you do not, read
[Terraform 101](../html/terraform-101.html) first, then the
[AWS primer](../html/aws-primer.html).

## Tier 1 — Basic (`basic/`)

| File | Covers | Labs |
|---|---|---|
| [`01-getting-started.md`](basic/01-getting-started.md) | IaC, the root module, HCL syntax, version constraints, authentication | lab00, lab01 |
| [`02-providers.md`](basic/02-providers.md) | `required_providers`, the lock file, resources vs data sources, provider upgrades | lab01 |
| [`03-resources.md`](basic/03-resources.md) | Resource addressing, dependencies, AMI lookups, security groups, tags | lab02, lab03 |
| [`04-workflow.md`](basic/04-workflow.md) | `init`, `plan`, `apply`, `destroy`, saved plans, when to re-init | lab04 |
| [`05-quality.md`](basic/05-quality.md) | `fmt`, `validate`, sensitive outputs, CI gates | lab05 |

Visual: [`../html/basic.html`](../html/basic.html)

## Tier 2 — Intermediate (`intermediate/`)

| File | Covers | Labs |
|---|---|---|
| [`06-variables.md`](intermediate/06-variables.md) | Typed variables, locals, value precedence, tfvars, sensitive | lab06, lab07 |
| [`07-state.md`](intermediate/07-state.md) | What state stores, refresh, drift, `state list`/`show`, `-replace` | lab08 |
| [`08-modules.md`](intermediate/08-modules.md) | Root vs child modules, module inputs and outputs, module addresses in state | lab09 |

Collections, functions, and dynamic blocks (lab10–lab12) are covered in
[`advanced/functions.md`](advanced/functions.md).

Visual: [`../html/intermediate.html`](../html/intermediate.html)

## Tier 3 — Advanced (`advanced/`)

| File | Covers | Labs |
|---|---|---|
| [`functions.md`](advanced/functions.md) | Built-in functions, `for_each`, `count` vs `for_each`, dynamic blocks | lab10, lab11, lab12 |
| [`provisioners.md`](advanced/provisioners.md) | `local-exec`, `remote-exec`, connection blocks, lifecycle hooks, better alternatives | lab14, lab15 |
| [`state.md`](advanced/state.md) | S3 backends, state keys, DynamoDB locking, workspaces, migration, remote state consumers | lab16–lab20 |
| [`projects.md`](advanced/projects.md) | Project layout, multiple providers, environment promotion, capstone patterns | lab13, lab21 |

Visual: [`../html/advanced.html`](../html/advanced.html)

---

## The two primers

Neither is tier-specific; both come before lab00.

| Order | Page | Covers |
|---|---|---|
| **1** | [Terraform 101](../html/terraform-101.html) | What Terraform is and who owns it, HCL and block anatomy, providers and how to add them, every version-constraint operator, `required_version` vs `required_providers`, the lock file, the CLI and plan symbols, state, drift |
| **2** | [AWS Primer](../html/aws-primer.html) | Region and availability zone, VPC and CIDR, public vs private subnets, internet gateway, route table, security group, EC2, key pair, IAM access keys — each with its Terraform resource type |
