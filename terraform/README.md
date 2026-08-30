# Terraform Track

**25 labs, `lab00`–`lab24`, in one sequence.** Start from zero AWS knowledge and build a public web
server entirely in code — VPC, internet gateway, route table, subnet, security group, and an EC2
instance that serves a page — at `lab10`, mid-track, then rebuild it on remote state at `lab22`.

| | |
|---|---|
| **Start here, 1st** | [`html/terraform-101.html`](html/terraform-101.html) — Terraform fundamentals from absolute zero |
| **Start here, 2nd** | [`html/aws-primer.html`](html/aws-primer.html) — AWS concepts, if you have never opened the console |
| **Concepts** | [`html/concepts.html`](html/concepts.html) — all 26 topics, `lab00`–`lab24`, one page, sticky topic index |
| **Track catalog** | [`html/index.html`](html/index.html) — all 25 labs, searchable |
| **Lab index** | [`labmanuals/README.md`](labmanuals/README.md) — the authoritative table |
| **Lab code** | [`labs/README.md`](labs/README.md) — one root module per lab |
| **Deep dives** | [`docs/README.md`](docs/README.md) — one flat numbered file per subject |

---

## Read these two pages before lab00

Both assume you know nothing, and they answer different questions. Read them in this order:

| Order | Page | Answers | Covers |
|---|---|---|---|
| **1** | [Terraform 101](html/terraform-101.html) | What am I actually running? | What Terraform is and who owns it, what HCL is and the anatomy of a block, what a provider is and how to add one, every version-constraint operator including `~>`, `required_version` vs `required_providers`, the lock file, the CLI commands and the plan symbols, what state is, and what drift means |
| **2** | [AWS Primer](html/aws-primer.html) | What is a VPC? | Region and availability zone, VPC and CIDR, public vs private subnets, internet gateway, route table, security group, EC2, key pair, IAM access keys — each with its Terraform resource type, plus the diagram of what `lab10` builds |
| **3** | [Lab 00](labmanuals/lab00-aws-setup-and-init.md) | Does my setup work? | Start typing: versions, access keys, first provider block, first `terraform init` |

---

## Tier labels

Run the labs in numeric order, `lab00` → `lab24`. Tier is a difficulty label attached to each lab,
not a separate track and not a page: every topic lives on the single
[concepts.html](html/concepts.html).

| Tier | Labs | Range | Concepts | You will be able to |
|---|---|---|---|---|
| **Basic** | 6 | `lab00`–`lab05` | [`lab00` onward](html/concepts.html#lab00-foundations) | Authenticate to AWS, declare a provider, create a first resource in a VPC you built, run the init / plan / apply / destroy loop, and pass `fmt` and `validate` |
| **Intermediate** | 7 | `lab06`–`lab12` | [`lab06` onward](html/concepts.html#lab06-variables-outputs) | Parameterise with variables and tfvars, handle secrets, read and reason about state, extract a module, build the end-to-end capstone at `lab10`, and generate resources from collections and functions |
| **Advanced** | 12 | `lab13`–`lab24` | [`lab13` onward](html/concepts.html#lab13-multi-provider) | Use several providers, run provisioners, split environments with workspaces, keep state in S3 with locking, migrate state, consume another stack's outputs, generate nested blocks dynamically, rebuild the capstone on a remote backend, manage an S3 bucket, and choose between `count` and `for_each` |

`lab03` and `lab06` each build their own VPC, subnets and security group, so neither depends on the
account holding a default VPC. Neither has an internet gateway or a public IP: their instances are
deliberately unreachable, and SSH is scoped to the VPC CIDR only. Public reachability is `lab10`'s
payoff. Only `lab15` and `lab21` still require a default VPC.

## Requirements

| Item | Value |
|---|---|
| Terraform | `>= 1.5.0`, and `>= 1.11.0` for `lab17`–`lab19` and `lab22`, which set `use_lockfile` |
| AWS provider | `~> 5.0` |
| AWS CLI | v2 |
| Region | `us-east-2` |
| Instance type | `t3.micro` |
| AMI | Amazon Linux 2023, resolved with `data "aws_ami"` |
| AWS account | An IAM user with an access key. Sandbox accounts are permission-scoped, so an `UnauthorizedOperation` on apply is a policy boundary, not a broken credential |

## Quick start

```bash
# 1. Credentials (lab00 explains every line of this)
unset AWS_PROFILE AWS_SESSION_TOKEN
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_DEFAULT_REGION="us-east-2"
aws sts get-caller-identity

# 2. First lab
cd terraform/labs/lab00-aws-setup-and-init
terraform init
```

Then open [`labmanuals/lab00-aws-setup-and-init.md`](labmanuals/lab00-aws-setup-and-init.md) and
work forward. Each manual ends with a link to the next.

## How the four directories fit together

| Directory | Use it for |
|---|---|
| [`html/`](html/index.html) | Four self-contained pages: the two primers, the catalog, and `concepts.html`. Concept, worked example, line-by-line explanation, link to the lab. Open them offline, print them |
| [`labmanuals/`](labmanuals/README.md) | The step-by-step manual you follow at the keyboard, with expected output after every command |
| [`labs/`](labs/README.md) | Runnable `.tf` code. Edit files here; do not paste configuration out of the manual |
| [`docs/`](docs/README.md) | Longer written notes, one flat numbered file per subject, for after the lab |

Read the HTML page, do the manual, run the code, then read the doc.

## Rules that apply to every lab

- Run Terraform from inside one lab directory. Sibling directories must not share state.
- Read every `plan` before approving it. An unexpected *destroy* or *forces replacement* means stop.
- Run `terraform destroy` when a lab that creates AWS resources is done. Charges accrue while it runs.
- Credentials never go in a `.tf` file, and state files never go in git.

## Regenerating the HTML

All four pages under `html/` are generated. Never hand-edit them — change the generator and re-run
it.

| Page | Generator |
|---|---|
| `index.html`, `concepts.html` | `curriculum/gen_terraform_html.py` |
| `terraform-101.html` | `curriculum/gen_terraform_101.py` |
| `aws-primer.html` | `curriculum/gen_aws_primer.py` |

```bash
python3 curriculum/gen_terraform_html.py
python3 curriculum/gen_terraform_101.py
python3 curriculum/gen_aws_primer.py
```

All three are safe to re-run at any time and byte-identical on repeat runs; each overwrites only its
own output. Shared CSS, the page shell, and the four-item nav live in `curriculum/tf_style.py`,
which guarantees every page looks identical. Changing the nav there means re-running all three
generators.

`gen_terraform_html.py` self-checks after writing: every lab-manual href resolves, every link stays
inside the four-page set, and every topic anchor on `concepts.html` has a matching card id and a
sticky-nav entry.
