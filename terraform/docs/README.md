# Terraform Concept Docs

Written deep dives, one flat sequence in lab reading order. Read the matching page in
[`../html/`](../html/index.html) first for the short version with a worked example, then come here
for the longer treatment, and do the lab in [`../labmanuals/`](../labmanuals/README.md).

These docs assume you already know what Terraform is. If you do not, read
[Terraform 101](../html/terraform-101.html) first, then the
[AWS primer](../html/aws-primer.html).

## The docs, in order

| # | Doc | Covers | Labs it backs |
|---|---|---|---|
| 00 | [`00-getting-started.md`](00-getting-started.md) | IaC, the root module, HCL syntax, version constraints, authentication | lab00, lab01 |
| 01 | [`01-providers.md`](01-providers.md) | `required_providers`, the lock file, resources vs data sources, the AMI lookup, provider aliases, and the console build lab02 does by hand | lab01, lab02 |
| 02 | [`02-resources.md`](02-resources.md) | Resource addressing, inferred dependencies, `depends_on`, naming the network instead of inheriting a default VPC, tags | lab03 |
| 03 | [`03-workflow.md`](03-workflow.md) | `init`, `plan`, `apply`, `destroy`, plan symbols, saved plans, when to re-init | lab04 |
| 04 | [`04-quality.md`](04-quality.md) | `fmt` exit codes, `validate`, how far a sensitive output is hidden, CI gates | lab05 |
| 05 | [`05-variables.md`](05-variables.md) | Typed variables, locals, value precedence, tfvars, `validation`, `sensitive`, `nonsensitive()` | lab06, lab07 |
| 06 | [`06-state.md`](06-state.md) | What state stores, secrets in plain text, refresh and drift, `state list`/`show`, `-replace` | lab08 |
| 07 | [`07-modules.md`](07-modules.md) | Root vs child modules, module inputs and outputs, module addresses in state | lab09 |
| 08 | [`08-capstone.md`](08-capstone.md) | The capstone build resource by resource, `user_data` versus a provisioner, `depends_on` | lab10 |
| 09 | [`09-collections-functions.md`](09-collections-functions.md) | list vs set vs map, `count` vs `for_each`, built-in functions, `for` expressions | lab11, lab12 |
| 10 | [`10-multi-provider.md`](10-multi-provider.md) | Several providers in one root module, and provider aliases | lab13 |
| 11 | [`11-provisioners.md`](11-provisioners.md) | `local-exec`, `remote-exec`, connection blocks, lifecycle hooks, better alternatives | lab14, lab15 |
| 12 | [`12-workspaces.md`](12-workspaces.md) | What a workspace isolates, `terraform.workspace`, why it is not an environment boundary | lab16 |
| 13 | [`13-remote-state.md`](13-remote-state.md) | S3 backends, native S3 locking, state keys, migration, remote state consumers, the capstone on a backend | lab17, lab18, lab19, lab20, lab22 |
| 14 | [`14-dynamic-blocks.md`](14-dynamic-blocks.md) | `dynamic` blocks, the block-named iterator, when to write blocks out literally | lab21 |
| 15 | [`15-s3-buckets.md`](15-s3-buckets.md) | Globally unique bucket names, the provider 5.x split into separate settings resources, `force_destroy` | lab23 |
| 16 | [`16-count-foreach.md`](16-count-foreach.md) | `count` by position vs `for_each` by key, on real buckets, with both captured plans | lab24 |
| 17 | [`17-project-structure.md`](17-project-structure.md) | Repository layout, one state per environment and component, environment promotion, project hygiene | reference — no single lab |

Visual companion for every topic above: [`../html/concepts.html`](../html/concepts.html).

## The two primers

Neither is tied to a lab; both come before lab00.

| Order | Page | Covers |
|---|---|---|
| **1** | [Terraform 101](../html/terraform-101.html) | What Terraform is and who owns it, HCL and block anatomy, providers and how to add them, every version-constraint operator, `required_version` vs `required_providers`, the lock file, the CLI and plan symbols, state, drift |
| **2** | [AWS Primer](../html/aws-primer.html) | Region and availability zone, VPC and CIDR, public vs private subnets, internet gateway, route table, security group, EC2, key pair, IAM access keys — each with its Terraform resource type |
