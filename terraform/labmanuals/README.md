# Terraform Lab Manuals — Index

**25 labs, `lab00`–`lab24`, one continuous sequence.** Work through them in numeric order; each lab
assumes the previous one is complete. The end-to-end capstone sits at `lab10`, mid-track, so the
earlier pieces come together before the tooling-heavy labs. Tier is a difficulty label in the table
below, not a separate path.

| | |
|---|---|
| **New to Terraform** | [`../html/terraform-101.html`](../html/terraform-101.html) — **read this first**, before lab00 |
| **New to AWS** | [`../html/aws-primer.html`](../html/aws-primer.html) — read this second |
| **Concepts** | [`../html/concepts.html`](../html/concepts.html) — all 26 topics, `lab00`–`lab24`, one page |
| **Lab code** | [`../labs/`](../labs/) — one root module per lab |
| **Concept docs** | [`../docs/`](../docs/) — flat numbered deep dives |
| **Track catalog** | [`../html/index.html`](../html/index.html) — searchable table of all 25 labs |

Terraform `>= 1.5.0`, AWS provider `~> 5.0`, region `us-east-2`, instance type `t3.micro`.

## Before lab00

Starting from zero, read both primers in this order — they answer different questions:

1. [Terraform 101](../html/terraform-101.html) — what Terraform is, HCL and block anatomy,
   providers, every version-constraint operator, the CLI and plan symbols, state, and drift.
2. [AWS Primer](../html/aws-primer.html) — region, VPC, CIDR, subnet, internet gateway, route
   table, security group, EC2, key pair, IAM access keys, plus the `lab10` architecture diagram.

Then keep [concepts.html](../html/concepts.html) open beside the manuals: every topic in lab order,
each with a worked example, a line-by-line explanation, and a link back to its lab.

---

## All 25 labs

The **Concepts** column links straight to that lab's card on the single
[`../html/concepts.html`](../html/concepts.html) page.

| Lab | Title | Tier | Topic | Code | Concepts |
|---|---|---|---|---|---|
| 00 | [AWS Setup and First Init](lab00-aws-setup-and-init.md) | Basic | AWS credentials, provider block, first `init` | [`labs/lab00-aws-setup-and-init/`](../labs/lab00-aws-setup-and-init/) | [`lab00`](../html/concepts.html#lab00-foundations) |
| 01 | [Providers and Initialization](lab01-providers-init.md) | Basic | `required_providers`, lock file, `validate` | [`labs/lab01-providers-init/`](../labs/lab01-providers-init/) | [`lab01`](../html/concepts.html#lab01-providers-init) |
| 02 | [Building a Network by Hand in the Console](lab02-console-vpc.md) | Basic | Manual console build, contrasted with IaC | [`labs/lab02-console-vpc/`](../labs/lab02-console-vpc/) (no `.tf`) | [`lab02`](../html/concepts.html#lab02-console-vpc) |
| 03 | [Your First EC2 Instance](lab03-first-ec2.md) | Basic | AMI data source, own VPC and subnets, security group, instance | [`labs/lab03-first-ec2/`](../labs/lab03-first-ec2/) | [`lab03`](../html/concepts.html#lab03-first-ec2) |
| 04 | [Plan, Apply, and Destroy](lab04-plan-apply-destroy.md) | Basic | The core workflow against a real VPC, no cloud cost | [`labs/lab04-plan-apply-destroy/`](../labs/lab04-plan-apply-destroy/) | [`lab04`](../html/concepts.html#lab04-plan-apply-destroy) |
| 05 | [Format and Validate](lab05-fmt-validate.md) | Basic | `fmt`, `validate`, CI-style quality gates | [`labs/lab05-fmt-validate/`](../labs/lab05-fmt-validate/) | [`lab05`](../html/concepts.html#lab05-fmt-validate) |
| 06 | [Variables and Outputs](lab06-variables-outputs.md) | Intermediate | Every variable type, locals, outputs, own VPC and subnet | [`labs/lab06-variables-outputs/`](../labs/lab06-variables-outputs/) | [`lab06`](../html/concepts.html#lab06-variables-outputs) |
| 07 | [tfvars and Secrets](lab07-tfvars-secrets.md) | Intermediate | tfvars files, precedence, `sensitive`, values as tags on a real VPC | [`labs/lab07-tfvars-secrets/`](../labs/lab07-tfvars-secrets/) | [`lab07`](../html/concepts.html#lab07-tfvars-secrets) |
| 08 | [Local State](lab08-local-state.md) | Intermediate | `terraform.tfstate`, refresh, drift, a real VPC ID in state | [`labs/lab08-local-state/`](../labs/lab08-local-state/) | [`lab08`](../html/concepts.html#lab08-local-state) |
| 09 | [Modules](lab09-modules.md) | Intermediate | Child modules, inputs, outputs | [`labs/lab09-modules/`](../labs/lab09-modules/) | [`lab09`](../html/concepts.html#lab09-modules) |
| 10 | [Capstone: VPC to public web server](lab10-capstone-vpc-ec2.md) | Intermediate | VPC, IGW, subnet, route table, SG, EC2 | [`labs/lab10-capstone-vpc-ec2/`](../labs/lab10-capstone-vpc-ec2/) | [`lab10`](../html/concepts.html#lab10-capstone-vpc-ec2) |
| 11 | [Collections](lab11-collections.md) | Intermediate | list vs set vs map, `for` expressions, a subnet from a map key | [`labs/lab11-collections/`](../labs/lab11-collections/) | [`lab11`](../html/concepts.html#lab11-collections) |
| 12 | [Functions](lab12-functions.md) | Intermediate | String, collection, CIDR, encoding, `cidrsubnet()` as a real subnet | [`labs/lab12-functions/`](../labs/lab12-functions/) | [`lab12`](../html/concepts.html#lab12-functions) |
| 13 | [Multi-provider configuration](lab13-multi-provider.md) | Advanced | Two providers, provider aliases | [`labs/lab13-multi-provider/`](../labs/lab13-multi-provider/) | [`lab13`](../html/concepts.html#lab13-multi-provider) |
| 14 | [local-exec provisioner](lab14-local-exec-provisioner.md) | Advanced | Run a command on the Terraform host | [`labs/lab14-local-exec-provisioner/`](../labs/lab14-local-exec-provisioner/) | [`lab14`](../html/concepts.html#lab14-local-exec-provisioner) |
| 15 | [remote-exec provisioner](lab15-remote-exec-provisioner.md) | Advanced | SSH `connection` block, inline commands | [`labs/lab15-remote-exec-provisioner/`](../labs/lab15-remote-exec-provisioner/) | [`lab15`](../html/concepts.html#lab15-remote-exec-provisioner) |
| 16 | [Workspaces](lab16-workspaces.md) | Advanced | `terraform.workspace`, per-env naming, one real VPC per workspace | [`labs/lab16-workspaces/`](../labs/lab16-workspaces/) | [`lab16`](../html/concepts.html#lab16-workspaces) |
| 17 | [S3 backend](lab17-s3-backend.md) | Advanced | Remote state in S3, backend config files | [`labs/lab17-s3-backend/`](../labs/lab17-s3-backend/) | [`lab17`](../html/concepts.html#lab17-s3-backend) |
| 18 | [State keys and locking](lab18-state-keys-locking.md) | Advanced | Key conventions, native S3 lockfile | [`labs/lab18-state-keys-locking/`](../labs/lab18-state-keys-locking/) | [`lab18`](../html/concepts.html#lab18-state-keys-locking) |
| 19 | [State migration](lab19-state-migration.md) | Advanced | `init -migrate-state`, backups, a real VPC that must not move | [`labs/lab19-state-migration/`](../labs/lab19-state-migration/) | [`lab19`](../html/concepts.html#lab19-state-migration) |
| 20 | [Remote state consumer](lab20-remote-state-consumer.md) | Advanced | `terraform_remote_state` data source | [`labs/lab20-remote-state-consumer/`](../labs/lab20-remote-state-consumer/) | [`lab20`](../html/concepts.html#lab20-remote-state-consumer) |
| 21 | [Dynamic Blocks](lab21-dynamic-blocks.md) | Advanced | Generated nested blocks from data | [`labs/lab21-dynamic-blocks/`](../labs/lab21-dynamic-blocks/) | [`lab21`](../html/concepts.html#lab21-dynamic-blocks) |
| 22 | [EC2 with remote state in S3](lab22-ec2-s3-backend.md) | Advanced | The capstone build, state kept in S3 | [`labs/lab22-ec2-s3-backend/`](../labs/lab22-ec2-s3-backend/) | [`lab22`](../html/concepts.html#lab22-ec2-s3-backend) |
| 23 | [S3 bucket as a Terraform resource](lab23-s3-bucket.md) | Advanced | `aws_s3_bucket`, versioning, encryption | [`labs/lab23-s3-bucket/`](../labs/lab23-s3-bucket/) | [`lab23`](../html/concepts.html#lab23-s3-bucket) |
| 24 | [count and for_each on real buckets](lab24-count-foreach-buckets.md) | Advanced | `count` by position vs `for_each` by name | [`labs/lab24-count-foreach-buckets/`](../labs/lab24-count-foreach-buckets/) | [`lab24`](../html/concepts.html#lab24-count-foreach-buckets) |

Deep-dive docs: [`../docs/`](../docs/) — one flat numbered file per subject.

---

## Totals

| Tier label | Labs | Range |
|---|---|---|
| Basic | 6 | lab00–lab05 |
| Intermediate | 7 | lab06–lab12 |
| Advanced | 12 | lab13–lab24 |
| **Total** | **25** | **lab00–lab24** |

## Networks and reachability

Every lab that touches the network builds its own VPC, so none depends on the account holding a
default VPC: `lab03`, `lab04`, `lab06`, `lab07`, `lab08`, `lab10`, `lab11`, `lab12`, `lab16`,
`lab19` and `lab22`. Only `lab15` and `lab21` still require a default VPC.

`lab03` and `lab06` create no internet gateway and no public IP, and scope SSH to the VPC CIDR only,
so their instances are deliberately unreachable. `lab10` is the first lab that produces something you
can open in a browser.

**VPC limit.** The default quota is five VPCs per region, and every lab above uses `us-east-2`.
Destroy each lab before starting the next and you will never hold more than one. The exception is
`lab16`, which holds **two** at once (one per workspace) and must stay applied until `lab20` has
read its state — so `lab17` through `lab19` run alongside those two. Every VPC in every lab is tagged
`Lab = "labNN"`, so you can audit what is outstanding:

```bash
aws ec2 describe-vpcs --region us-east-2 \
  --filters 'Name=tag-key,Values=Lab' \
  --query 'Vpcs[].[VpcId,Tags[?Key==`Lab`].Value|[0]]' --output table
```

## Cost control

Each manual's **What you will build** table states the cost of every resource it creates. Any lab
that creates an EC2 instance or an S3 bucket bills while it runs — finish with `terraform destroy`
in that lab's directory. `lab00`, `lab01`, `lab04`, `lab05`, `lab07`, `lab08`, `lab11`, `lab12`,
`lab16` and `lab19` create nothing billable — a VPC, subnet, security group and route table are all
free — and `lab02` is console-only with no `.tf` files. Free is not the same as disposable: those
VPCs are real, they count against the region's quota, and every lab's Cleanup section destroys
them. `lab10` and `lab22` build the same billable topology
and `lab23` leaves a versioned bucket behind, so destroy each of them the moment you have seen the
result.
