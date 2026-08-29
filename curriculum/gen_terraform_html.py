#!/usr/bin/env python3
"""Generate the Terraform track HTML: index + the three tier concept pages.

Output (all under terraform/html/):
    index.html          track catalog: entry-point sequence, tier cards, 22-lab table, search
    basic.html          Tier 1 concepts (lab00-lab05)
    intermediate.html   Tier 2 concepts (lab06-lab12)
    advanced.html       Tier 3 concepts (lab13-lab21)

The other two pages in the six-page set are generated elsewhere and are only linked from here:
terraform-101.html by gen_terraform_101.py, aws-primer.html by gen_aws_primer.py.

Every topic section follows the mandated four-part flow via tf_style.topic():
concept overview -> example code block -> line-by-line explanation -> lab link.

Re-runnable: each run overwrites its four files with byte-identical output for
identical input. No state is kept on disk.

    python3 curriculum/gen_terraform_html.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tf_style import esc, page, topic  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "terraform" / "html"

TF_FLOOR = "Terraform &gt;= 1.5.0"
AWS_PIN = "AWS provider ~&gt; 5.0"

# The complete Terraform HTML page set. index/basic/intermediate/advanced are written by this
# script; terraform-101 and aws-primer are written by their own generators. No other Terraform
# HTML page exists, so nothing here may link outside this set.
HTML_PAGES = [
    "index.html",
    "terraform-101.html",
    "aws-primer.html",
    "basic.html",
    "intermediate.html",
    "advanced.html",
]

# ---------------------------------------------------------------------------
# Locked 22-lab sequence (tf-aug2026-spec.md). num, slug, title, tier, topic
# ---------------------------------------------------------------------------
LABS = [
    (0, "lab00-aws-setup-and-init", "AWS Setup and Init", "basic",
     "Credentials, provider block, first init"),
    (1, "lab01-providers-init", "Providers and Init", "basic",
     "required_providers, lock file, validate"),
    (2, "lab02-console-vpc", "Console VPC", "basic",
     "Manual console build, contrasted with IaC"),
    (3, "lab03-first-ec2", "First EC2 Instance", "basic",
     "AMI data source, security group, instance"),
    (4, "lab04-plan-apply-destroy", "Plan, Apply, Destroy", "basic",
     "The core workflow with no cloud cost"),
    (5, "lab05-fmt-validate", "Format and Validate", "basic",
     "fmt, validate, CI-style quality gates"),
    (6, "lab06-variables-outputs", "Variables and Outputs", "intermediate",
     "Typed inputs, locals, outputs"),
    (7, "lab07-tfvars-secrets", "tfvars and Secrets", "intermediate",
     "tfvars files, precedence, sensitive"),
    (8, "lab08-local-state", "Local State", "intermediate",
     "terraform.tfstate, refresh, drift"),
    (9, "lab09-modules", "Modules", "intermediate",
     "Child modules, inputs, outputs"),
    (10, "lab10-collections", "Collections", "intermediate",
     "for_each over maps and sets"),
    (11, "lab11-functions", "Functions", "intermediate",
     "String, collection, CIDR, encoding"),
    (12, "lab12-dynamic-blocks", "Dynamic Blocks", "intermediate",
     "Generated nested blocks from data"),
    (13, "lab13-multi-provider", "Multiple Providers", "advanced",
     "Two providers, provider aliases"),
    (14, "lab14-local-exec-provisioner", "local-exec Provisioner", "advanced",
     "Run a command on the Terraform host"),
    (15, "lab15-remote-exec-provisioner", "remote-exec Provisioner", "advanced",
     "SSH connection block, inline commands"),
    (16, "lab16-workspaces", "Workspaces", "advanced",
     "terraform.workspace, per-env naming"),
    (17, "lab17-s3-backend", "S3 Backend", "advanced",
     "Remote state in S3, backend config files"),
    (18, "lab18-state-keys-locking", "State Keys and Locking", "advanced",
     "Key conventions, S3 native lockfile"),
    (19, "lab19-state-migration", "State Migration", "advanced",
     "init -migrate-state, backups"),
    (20, "lab20-remote-state-consumer", "Remote State Consumer", "advanced",
     "terraform_remote_state data source"),
    (21, "lab21-capstone-vpc-ec2", "Capstone: VPC and EC2", "advanced",
     "VPC, IGW, subnet, route table, SG, EC2"),
]

TIERS = {
    "basic": {
        "label": "Basic",
        "range": "lab00-lab05",
        "blurb": "Install, authenticate, declare a provider, create your first resource, "
                 "and learn the init / plan / apply / destroy loop.",
    },
    "intermediate": {
        "label": "Intermediate",
        "range": "lab06-lab12",
        "blurb": "Parameterise configuration with variables and tfvars, read state, extract "
                 "modules, and generate resources from collections.",
    },
    "advanced": {
        "label": "Advanced",
        "range": "lab13-lab21",
        "blurb": "Multiple providers, provisioners, workspaces, remote state in S3 with "
                 "locking, state migration, and the end-to-end capstone.",
    },
}


def lab_by_num(num: int):
    for lab in LABS:
        if lab[0] == num:
            return lab
    raise KeyError(num)


def manual_href(num: int) -> str:
    return f"../labmanuals/{lab_by_num(num)[1]}.md"


def lab_label(num: int) -> str:
    lab = lab_by_num(num)
    return f"Lab {num:02d} &mdash; {lab[2]}"


def practises(num: int) -> tuple[str, str]:
    return manual_href(num), lab_label(num)


# ---------------------------------------------------------------------------
# Tier 1 — Basic
# ---------------------------------------------------------------------------
BASIC_TOPICS = [
    dict(
        eyebrow="Lab 00 &middot; Foundations",
        heading="Infrastructure as code, and what a root module is",
        concept=(
            "Terraform is a declarative <em>infrastructure as code</em> (IaC) tool: you write the "
            "end state you want in HashiCorp Configuration Language (HCL) and Terraform makes the "
            "real cloud match it. A directory of <code class=\"inline\">.tf</code> files that you "
            "run Terraform in is called a <em>root module</em> &mdash; every lab in this track is "
            "one root module with its own state, so experiments never collide. "
            "<em>State</em> is the JSON file where Terraform records which real cloud object "
            "corresponds to each block you wrote."
        ),
        code=esc('''terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# A data source reads; it creates nothing and costs nothing.
data "aws_caller_identity" "current" {}

output "account_id" {
  description = "The AWS account number your credentials belong to."
  value       = data.aws_caller_identity.current.account_id
}'''),
        rows=[
            ("terraform {", "Settings block for Terraform itself. It configures the tool, not any cloud resource."),
            ("required_version", "Refuses to run on a CLI older than 1.5.0, so the whole class behaves identically."),
            ("required_providers", "Names each plugin the configuration needs. <code class=\"inline\">terraform init</code> downloads exactly these."),
            ("source = \"hashicorp/aws\"", "Registry address of the plugin that talks to the AWS API."),
            ("version = \"~&gt; 5.0\"", "Accepts any 5.x release and refuses 6.0, so a major provider change cannot break the lab silently."),
            ("provider \"aws\"", "Runtime configuration for that plugin. Region only &mdash; credentials never belong in a <code class=\"inline\">.tf</code> file."),
            ("data \"aws_caller_identity\"", "Read-only lookup of who Terraform is authenticated as. Proof the credentials work, with nothing created."),
            ("output \"account_id\"", "Prints a value after apply. Useful for humans and for other configurations."),
        ],
        lab=0,
    ),
    dict(
        eyebrow="Lab 00 &middot; Authentication",
        heading="AWS credentials: access keys and the environment variables",
        concept=(
            "An AWS <em>access key</em> is a pair of strings: the access key ID (public, starts "
            "<code class=\"inline\">AKIA</code>) and the secret access key (private, shown once). "
            "Terraform reads them from the environment through the standard AWS SDK credential "
            "chain, which is why the provider block only needs a region. Never put either value "
            "in a <code class=\"inline\">.tf</code> file or in git. If "
            "<code class=\"inline\">AWS_PROFILE</code> is already exported it overrides these "
            "variables, so unset it first."
        ),
        code=esc('''unset AWS_PROFILE AWS_SESSION_TOKEN

export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_DEFAULT_REGION="us-east-1"

aws sts get-caller-identity
# {
#     "UserId": "AIDA...",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/tf-labs"
# }

terraform init'''),
        rows=[
            ("unset AWS_PROFILE", "Removes any named profile from the environment. A leftover profile wins over the key variables and sends Terraform at the wrong account."),
            ("unset AWS_SESSION_TOKEN", "Clears a stale temporary-credential token, which otherwise fails with an expired-token error."),
            ("export AWS_ACCESS_KEY_ID", "The public half of the key pair. Identifies the IAM user."),
            ("export AWS_SECRET_ACCESS_KEY", "The private half. Treat it like a password; rotate it when the lab ends."),
            ("export AWS_DEFAULT_REGION", "Default region for the AWS CLI. The provider block sets Terraform's own region."),
            ("aws sts get-caller-identity", "Confirms the credentials resolve to a real identity before Terraform is involved."),
            ("terraform init", "Downloads the pinned providers into <code class=\"inline\">.terraform/</code> and writes <code class=\"inline\">.terraform.lock.hcl</code>."),
        ],
        lang_note="Setting <code class=\"inline\">AWS_PROFILE=\"\"</code> is not the same as unsetting it: an "
                  "empty value produces <code class=\"inline\">The config profile () could not be found</code>. "
                  "A named profile (<code class=\"inline\">aws configure --profile tf-labs</code> plus "
                  "<code class=\"inline\">profile = \"tf-labs\"</code> in the provider block) is the "
                  "documented alternate path.",
        lab=0,
    ),
    dict(
        eyebrow="Lab 01 &middot; Providers",
        heading="Providers, version pinning, and the lock file",
        concept=(
            "A <em>provider</em> is a plugin that translates your HCL into API calls for one system "
            "&mdash; AWS, or the <code class=\"inline\">random</code> provider that just generates "
            "values locally. Without a provider Terraform can build a dependency graph but cannot "
            "change anything. After <code class=\"inline\">terraform init</code>, the file "
            "<code class=\"inline\">.terraform.lock.hcl</code> records the exact provider builds "
            "and their checksums so every machine installs the same bytes."
        ),
        code=esc('''terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "random_pet" "lab_id" {
  length = 2
}

output "lab_id" {
  value = random_pet.lab_id.id
}'''),
        rows=[
            ("two entries in required_providers", "Both plugins are downloaded by <code class=\"inline\">init</code>. Declaring AWS here without using it yet keeps every later lab on the same pattern."),
            ("random = { ... }", "The random provider needs no credentials and creates nothing billable, so it is safe for a first apply."),
            ("resource \"random_pet\" \"lab_id\"", "<code class=\"inline\">random_pet</code> is the type, <code class=\"inline\">lab_id</code> is your name for it. Together they form the address <code class=\"inline\">random_pet.lab_id</code>."),
            ("length = 2", "Number of words in the generated name, for example <code class=\"inline\">quick-hound</code>."),
            ("value = random_pet.lab_id.id", "Reads the <code class=\"inline\">id</code> attribute off the resource. This reference is also what makes Terraform order the graph correctly."),
        ],
        lang_note="Commit <code class=\"inline\">.terraform.lock.hcl</code>. Never commit "
                  "<code class=\"inline\">.terraform/</code> &mdash; it is a download cache and can be "
                  "rebuilt with <code class=\"inline\">terraform init</code> at any time.",
        lab=1,
    ),
    dict(
        eyebrow="Lab 02 &middot; Console vs code",
        heading="Why the console does not scale: build a VPC by hand once",
        concept=(
            "A <em>VPC</em> (Virtual Private Cloud) is your own private network inside an AWS "
            "region, defined by a CIDR range such as <code class=\"inline\">10.0.0.0/16</code>. "
            "Lab 02 builds one entirely by clicking in the AWS console, on purpose: it is the "
            "control experiment. Nothing records what you did, nothing can review it, and nothing "
            "can rebuild it. The commands below only read back what your clicking produced."
        ),
        code=esc('''aws ec2 describe-vpcs \\
  --filters "Name=tag:Name,Values=console-vpc" \\
  --query "Vpcs[].{Id:VpcId,Cidr:CidrBlock}" \\
  --output table

aws ec2 describe-subnets \\
  --filters "Name=vpc-id,Values=vpc-0abc123def456789a" \\
  --query "Subnets[].{Id:SubnetId,Cidr:CidrBlock,AZ:AvailabilityZone}" \\
  --output table'''),
        rows=[
            ("describe-vpcs", "Lists VPCs. The console gave you no artefact, so a query is the only way to describe what now exists."),
            ("--filters Name=tag:Name", "Finds the VPC by the <code class=\"inline\">Name</code> tag you typed in the console. Untagged console resources are effectively anonymous."),
            ("--query \"Vpcs[].{...}\"", "JMESPath expression that trims the response to the ID and CIDR."),
            ("describe-subnets", "Lists the subnets inside that VPC and the availability zone each one sits in."),
            ("vpc-0abc123def456789a", "A generated ID. Nobody chose it and nothing outside AWS knows it &mdash; the exact problem state files solve."),
        ],
        lang_note="This lab has no <code class=\"inline\">.tf</code> files. Lab 21 builds the same "
                  "network in code, and the difference in reviewability and repeatability is the "
                  "whole point of the exercise.",
        lab=2,
    ),
    dict(
        eyebrow="Lab 03 &middot; Resources",
        heading="Resources, data sources, and your first EC2 instance",
        concept=(
            "A <em>resource</em> is an object Terraform owns: it creates it, records its ID in "
            "state, updates it, and destroys it. A <em>data source</em> is a read-only query "
            "against something that already exists. An <em>AMI</em> (Amazon Machine Image) is the "
            "disk image an EC2 instance boots from, and its ID differs per region, so resolve it "
            "with <code class=\"inline\">data \"aws_ami\"</code> instead of hardcoding an ID. This "
            "lab is deliberately the minimum viable AWS build: one data source and one resource, "
            "so a plan proposes exactly one thing to create."
        ),
        code=esc('''data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type

  tags = {
    Name      = var.instance_name
    Lab       = "lab03"
    ManagedBy = "Terraform"
  }
}'''),
        rows=[
            ("data \"aws_ami\" \"amazon_linux\"", "Asks EC2 for a matching image at plan time. Nothing is created and nothing enters state as a managed object."),
            ("most_recent = true", "Several images match the filter; take the newest published one."),
            ("owners = [\"amazon\"]", "Restricts the search to images published by AWS itself, so a look-alike community AMI cannot be selected."),
            ("filter { name = \"name\" }", "Matches the Amazon Linux 2023 x86_64 naming pattern. The <code class=\"inline\">*</code> absorbs the date portion of the name."),
            ("filter { virtualization-type }", "Restricts to HVM images, the only virtualization type current instance families support."),
            ("ami = data.aws_ami.amazon_linux.id", "Consumes the data source result. The <code class=\"inline\">data.</code> prefix is what distinguishes a lookup from a managed resource."),
            ("instance_type = var.instance_type", "Defaults to <code class=\"inline\">t3.micro</code>, the smallest general-purpose size used throughout this track."),
            ("no subnet_id", "Nothing places this instance in a network, so EC2 puts it in the region's <em>default VPC</em>. See the note below &mdash; this is the one way this lab can fail."),
            ("no security group", "None is declared, so the instance gets the default VPC's default group. Lab 12 builds a group on its own; Lab 21 builds one inside a VPC it created."),
            ("tags = { Lab = \"lab03\" }", "Every AWS resource in this track carries <code class=\"inline\">Name</code> and <code class=\"inline\">Lab</code> tags so leftovers are easy to find and delete."),
        ],
        lang_note=(
            "<strong>This lab needs a default VPC.</strong> An "
            "<code class=\"inline\">aws_instance</code> with no "
            "<code class=\"inline\">subnet_id</code> is placed in the region's default VPC, and a "
            "fresh training account may have none. <code class=\"inline\">terraform plan</code> "
            "does not detect this; the apply fails with "
            "<code class=\"inline\">VPCIdNotSpecified: No default VPC for this user</code>. "
            "Labs 03, 06 and 12 all depend on it. Verify with "
            "<code class=\"inline\">aws ec2 describe-vpcs --filters Name=isDefault,Values=true "
            "--query 'Vpcs[].VpcId' --output text</code> and create one with "
            "<code class=\"inline\">aws ec2 create-default-vpc</code> if the result is empty."
        ),
        lab=3,
    ),
    dict(
        eyebrow="Lab 04 &middot; Workflow",
        heading="The core loop: init, plan, apply, destroy",
        concept=(
            "Terraform is not a daemon; you invoke it. <code class=\"inline\">init</code> installs "
            "providers, <code class=\"inline\">plan</code> is a dry run that prints the diff "
            "between your files and reality, <code class=\"inline\">apply</code> executes that "
            "diff, and <code class=\"inline\">destroy</code> removes everything the directory "
            "manages. The habit to build is propose-then-commit: read every plan before you "
            "approve it, and always destroy an AWS lab when you finish it."
        ),
        code=esc('''terraform init
terraform plan
# Plan: 1 to add, 0 to change, 0 to destroy.

terraform apply
# Enter a value: yes
# random_string.example: Creation complete after 0s
# Outputs:
# generated_value = "kf3mzq8dvwrt"

terraform plan
# No changes. Your infrastructure matches the configuration.

terraform plan -out=tfplan
terraform apply tfplan

terraform destroy'''),
        rows=[
            ("terraform init", "First command in any new directory. Installs providers and prepares the backend. Re-run it whenever <code class=\"inline\">required_providers</code> or the backend changes."),
            ("terraform plan", "Refreshes state from the API, compares it to your files, and prints the actions. It changes nothing."),
            ("Plan: 1 to add, ...", "The summary line to read first. Any unexpected <em>destroy</em> or <em>forces replacement</em> means stop and investigate."),
            ("terraform apply", "Re-plans, prompts for <code class=\"inline\">yes</code>, then executes. Resource IDs land in <code class=\"inline\">terraform.tfstate</code>."),
            ("second terraform plan", "Reports no changes. That idempotency is the proof state and configuration agree."),
            ("plan -out=tfplan", "Saves the exact diff to a file, so the applied change cannot differ from the reviewed one. This is the CI pattern."),
            ("apply tfplan", "Applies the saved plan with no prompt and no re-planning."),
            ("terraform destroy", "Plans and executes the removal of every resource in this directory's state."),
        ],
        lab=4,
    ),
    dict(
        eyebrow="Lab 05 &middot; Quality",
        heading="fmt and validate: the two gates before every plan",
        concept=(
            "<code class=\"inline\">terraform fmt</code> rewrites your files into canonical HCL "
            "style, so code review shows logic changes rather than indentation noise. "
            "<code class=\"inline\">terraform validate</code> checks that blocks, argument names, "
            "types, and references are internally consistent &mdash; it needs "
            "<code class=\"inline\">init</code> first because it reads provider schemas, but it "
            "makes no API calls. Think of it as: fmt is style, validate is grammar, plan is "
            "meaning against live infrastructure."
        ),
        code=esc('''terraform fmt -recursive
# main.tf

terraform fmt -check -diff
# exits 0 when every file is already formatted

terraform init -backend=false
terraform validate
# Success! The configuration is valid.

# The output this lab formats and then hides:
output "formatted_example" {
  value     = random_string.formatted_example.result
  sensitive = true
}'''),
        rows=[
            ("terraform fmt -recursive", "Formats the current directory and every subdirectory in place, and prints the names of files it changed."),
            ("terraform fmt -check -diff", "Changes nothing, exits non-zero if formatting is needed, and shows the diff. This is the CI form."),
            ("init -backend=false", "Installs providers without configuring remote state, which is what a validate-only job needs and all it should be allowed to do."),
            ("terraform validate", "Catches unknown arguments, wrong types, and references to resources that do not exist. It cannot catch a missing AMI or an IAM denial."),
            ("sensitive = true", "Redacts the value in CLI output and in <code class=\"inline\">terraform output</code>. The value is still stored in plain text in state."),
        ],
        lang_note="A green <code class=\"inline\">validate</code> does not imply a green "
                  "<code class=\"inline\">plan</code>. Only <code class=\"inline\">plan</code> "
                  "contacts AWS, so quota errors, permission boundaries, and drift surface there.",
        lab=5,
    ),
]

# ---------------------------------------------------------------------------
# Tier 2 — Intermediate
# ---------------------------------------------------------------------------
INTERMEDIATE_TOPICS = [
    dict(
        eyebrow="Lab 06 &middot; Inputs",
        heading="Variables, locals, and outputs",
        concept=(
            "An <em>input variable</em> is a knob on your configuration: declare it with a "
            "<code class=\"inline\">type</code> and a <code class=\"inline\">description</code>, "
            "then the same code can build training and production by passing different values. A "
            "<em>local</em> is a computed value used inside the module only &mdash; ideal for "
            "merged tag maps. An <em>output</em> exports a value after apply for operators or for "
            "another configuration to read."
        ),
        code=esc('''variable "instance_name" {
  type        = string
  description = "Name tag applied to the instance and its security group."
  default     = "variables-lab-web"
}

variable "tags" {
  type        = map(string)
  description = "Organisation tags merged onto every resource."
  default = {
    Environment = "training"
    Owner       = "platform-team"
  }
}

locals {
  common_tags = merge(var.tags, {
    Name = var.instance_name
    Lab  = "lab06"
  })
}

resource "aws_instance" "web" {
  ami           = data.aws_ami.al2023.id
  instance_type = "t3.micro"
  tags          = local.common_tags
}

output "instance_id" {
  description = "EC2 instance ID, for the console and for later labs."
  value       = aws_instance.web.id
}'''),
        rows=[
            ("variable \"instance_name\"", "Declares an input. Its address elsewhere in the configuration is <code class=\"inline\">var.instance_name</code>."),
            ("type = string", "Terraform rejects a non-string value at plan time instead of failing mid-apply. Every variable in this track declares a type."),
            ("description", "Required by the track's own rules: it is the documentation a module consumer reads."),
            ("default", "Makes the variable optional. Omit the default when a value must always be supplied deliberately."),
            ("type = map(string)", "A map of string keys to string values, written <code class=\"inline\">{ Key = \"value\" }</code> in HCL."),
            ("locals { ... }", "Values computed once and reused. Not settable from outside the module."),
            ("merge(var.tags, { ... })", "Combines maps into one. On a key collision the later map wins, so <code class=\"inline\">Name</code> here overrides any inherited <code class=\"inline\">Name</code>."),
            ("tags = local.common_tags", "One reference gives every resource the same tag set. Change <code class=\"inline\">var.tags</code> once and all of them update."),
            ("output \"instance_id\"", "Printed after apply and readable with <code class=\"inline\">terraform output instance_id</code>."),
        ],
        lab=6,
    ),
    dict(
        eyebrow="Lab 07 &middot; Values and secrets",
        heading="tfvars files, value precedence, and sensitive",
        concept=(
            "A <em>tfvars</em> file supplies values for your variables without editing the code. "
            "<code class=\"inline\">terraform.tfvars</code> is loaded automatically; any other "
            "file needs <code class=\"inline\">-var-file</code>. Marking a variable or output "
            "<code class=\"inline\">sensitive = true</code> keeps its value out of CLI output and "
            "plan logs, but <strong>not</strong> out of the state file, so state must be protected "
            "as if it contained the secret &mdash; because it does."
        ),
        code=esc('''# variables.tf
variable "db_password" {
  type        = string
  description = "Database password, supplied at runtime."
  sensitive   = true
}

# terraform.tfvars.example  -> copy to terraform.tfvars, never commit the copy
# instance_name = "demo-web"
# db_password   = "replace-me"

# outputs.tf
output "connection_string" {
  description = "Redacted in CLI output; still stored in plain text in state."
  value       = "postgres://app:${var.db_password}@db.internal:5432/app"
  sensitive   = true
}'''),
        rows=[
            ("sensitive = true (variable)", "Terraform refuses to print the value in plan or apply output and marks anything derived from it as sensitive too."),
            ("no default", "Forces the value to be supplied explicitly. Terraform prompts if it is missing rather than silently using a placeholder."),
            ("terraform.tfvars.example", "The committed template. The real <code class=\"inline\">terraform.tfvars</code> is gitignored."),
            ("${var.db_password}", "String interpolation. Because the input is sensitive, the whole interpolated string is sensitive."),
            ("sensitive = true (output)", "Required here: Terraform errors out if an output derives from a sensitive value without this flag."),
            ("precedence, highest first", "<code class=\"inline\">-var</code> and <code class=\"inline\">-var-file</code>, then <code class=\"inline\">*.auto.tfvars</code> alphabetically, then <code class=\"inline\">terraform.tfvars</code>, then <code class=\"inline\">TF_VAR_name</code> environment variables, then the block <code class=\"inline\">default</code>."),
            ("TF_VAR_db_password", "The environment-variable form. Preferred in CI, where the value comes from a secret store and never touches disk."),
        ],
        lab=7,
    ),
    dict(
        eyebrow="Lab 08 &middot; State",
        heading="Local state, refresh, and drift",
        concept=(
            "<em>State</em> is Terraform's memory: a JSON file mapping each address in your "
            "configuration to the real object's ID and last-known attributes. Without it, "
            "Terraform could not tell whether to create a second VPC or update the existing one. "
            "With no <code class=\"inline\">backend</code> block the state is a local "
            "<code class=\"inline\">terraform.tfstate</code> beside your files. <em>Drift</em> is "
            "when someone changes infrastructure outside Terraform; the next plan shows it."
        ),
        code=esc('''terraform apply

terraform state list
# random_pet.first

terraform state show random_pet.first
# resource "random_pet" "first" {
#     id     = "state-lab-clever-mongoose"
#     length = 2
#     prefix = "state-lab"
# }

terraform plan -refresh-only

terraform apply -replace=random_pet.first

cp terraform.tfstate terraform.tfstate.backup.manual'''),
        rows=[
            ("terraform state list", "Prints every address Terraform manages here. The first command to run when you are unsure what a directory owns."),
            ("terraform state show ADDR", "Prints the recorded attributes for one address. Safer and clearer than opening the JSON."),
            ("plan -refresh-only", "Updates state from the API and reports drift without proposing configuration changes. This is how you detect console edits."),
            ("apply -replace=ADDR", "Destroys and recreates one resource without editing code. Replaces the deprecated <code class=\"inline\">terraform taint</code>."),
            ("cp terraform.tfstate ...", "Manual backup before any risky state operation. Terraform also writes <code class=\"inline\">terraform.tfstate.backup</code> automatically."),
            ("no backend block", "Means local state. Fine for one person; Tier 3 moves it to S3 so a team and CI can share it."),
        ],
        lang_note="Never hand-edit <code class=\"inline\">terraform.tfstate</code>, and never commit it: "
                  "it holds resource IDs and any value marked sensitive, in plain text.",
        lab=8,
    ),
    dict(
        eyebrow="Lab 09 &middot; Modules",
        heading="Child modules: inputs in, outputs out",
        concept=(
            "A <em>module</em> is a directory of Terraform configuration with its own variables and "
            "outputs. The directory you run <code class=\"inline\">apply</code> in is the "
            "<em>root module</em>; one it calls through a <code class=\"inline\">module</code> "
            "block is a <em>child module</em>. Everything inside a child is private unless it is "
            "exported as an output, which is what lets a network team own the VPC pattern while "
            "application teams only consume its IDs."
        ),
        code=esc('''# root main.tf
module "network" {
  source      = "./modules/network"
  name        = var.name
  vpc_cidr    = "10.0.0.0/16"
  subnet_cidr = "10.0.1.0/24"
}

output "vpc_id" {
  value = module.network.vpc_id
}

# modules/network/main.tf
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true

  tags = { Name = "${var.name}-vpc", Lab = "lab09" }
}

resource "aws_subnet" "this" {
  vpc_id     = aws_vpc.this.id
  cidr_block = var.subnet_cidr

  tags = { Name = "${var.name}-subnet", Lab = "lab09" }
}

# modules/network/outputs.tf
output "vpc_id" {
  description = "ID of the VPC this module created."
  value       = aws_vpc.this.id
}'''),
        rows=[
            ("module \"network\"", "Calls a child module and names this call <code class=\"inline\">network</code>. Calling it twice with different names creates two independent copies."),
            ("source = \"./modules/network\"", "A local path. Modules can also come from the Terraform Registry or a git URL, which is how they get versioned."),
            ("name / vpc_cidr / subnet_cidr", "Arguments that must match <code class=\"inline\">variable</code> blocks declared inside the child. Anything else is an error."),
            ("module.network.vpc_id", "The only way the root reads a child value: through a declared output. Reaching directly at <code class=\"inline\">aws_vpc.this</code> inside the child is not possible."),
            ("vpc_id = aws_vpc.this.id", "Inside the child, the subnet references the VPC, so Terraform creates the VPC first without any <code class=\"inline\">depends_on</code>."),
            ("state addresses", "Child resources are stored as <code class=\"inline\">module.network.aws_vpc.this</code>. The module path is part of the address."),
        ],
        lab=9,
    ),
    dict(
        eyebrow="Lab 10 &middot; Collections",
        heading="for_each: one block, many resources",
        concept=(
            "<code class=\"inline\">for_each</code> creates one copy of a resource per entry in a "
            "map or set, so three subnets need one block rather than three. Inside the block, "
            "<code class=\"inline\">each.key</code> is the entry's key and "
            "<code class=\"inline\">each.value</code> is its value. Because the address includes "
            "the key, removing one entry does not disturb the others &mdash; which is exactly what "
            "goes wrong with <code class=\"inline\">count</code> and its integer indexes."
        ),
        code=esc('''variable "subnets" {
  type = map(object({
    cidr = string
    az   = string
  }))
  description = "Public subnets keyed by short name."
  default = {
    app_a = { cidr = "10.0.1.0/24", az = "us-east-1a" }
    app_b = { cidr = "10.0.2.0/24", az = "us-east-1b" }
  }
}

resource "aws_subnet" "public" {
  for_each = var.subnets

  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value.cidr
  availability_zone = each.value.az

  tags = { Name = "public-${each.key}", Lab = "lab10" }
}

output "subnet_ids" {
  value = { for name, subnet in aws_subnet.public : name => subnet.id }
}'''),
        rows=[
            ("map(object({ ... }))", "A map whose values are structured. Terraform checks at plan time that every entry has a <code class=\"inline\">cidr</code> and an <code class=\"inline\">az</code> of the right type."),
            ("for_each = var.subnets", "Creates one subnet per map entry. Addresses become <code class=\"inline\">aws_subnet.public[\"app_a\"]</code>."),
            ("each.key", "The map key, <code class=\"inline\">app_a</code>. Used here to build a distinct Name tag."),
            ("each.value.cidr", "A field of the entry's object value."),
            ("{ for name, subnet in ... }", "A <em>for expression</em> that builds a new map by iterating the created resources."),
            ("name =&gt; subnet.id", "Sets each output entry's key and value, giving a clean <code class=\"inline\">{ app_a = \"subnet-...\" }</code> map."),
            ("why not count", "<code class=\"inline\">count</code> addresses by position, so deleting the middle element renumbers and recreates the rest. Prefer <code class=\"inline\">for_each</code> for anything named."),
        ],
        lab=10,
    ),
    dict(
        eyebrow="Lab 11 &middot; Functions",
        heading="Built-in functions transform values at plan time",
        concept=(
            "HCL has no loops or user-defined functions, but it ships a large library of built-in "
            "ones for strings, collections, CIDR arithmetic, and encoding. They evaluate during "
            "plan, so results are visible before anything is created. "
            "<code class=\"inline\">terraform console</code> gives you an interactive prompt to "
            "test an expression before you commit it to a file."
        ),
        code=esc('''variable "application" {
  type        = string
  description = "Human-readable application name."
  default     = "Payments API"
}

variable "cidrs" {
  type        = list(string)
  description = "Candidate CIDR ranges, possibly duplicated and unordered."
  default     = ["10.0.2.0/24", "10.0.1.0/24", "10.0.1.0/24"]
}

locals {
  slug          = lower(replace(var.application, " ", "-"))
  unique_cidrs  = sort(tolist(toset(var.cidrs)))
  subnet_prefix = cidrsubnet("10.20.0.0/16", 8, 12)
  configuration = jsonencode({ name = local.slug, cidrs = local.unique_cidrs })
}'''),
        rows=[
            ("replace(var.application, \" \", \"-\")", "Swaps every space for a hyphen: <code class=\"inline\">Payments-API</code>."),
            ("lower(...)", "Lowercases the result, giving the DNS-safe slug <code class=\"inline\">payments-api</code>. Functions nest inside out."),
            ("toset(var.cidrs)", "Converts the list to a set, which discards the duplicate <code class=\"inline\">10.0.1.0/24</code>."),
            ("tolist(...) then sort(...)", "Back to a list, then ordered, so the value is stable between plans and the diff stays empty."),
            ("cidrsubnet(\"10.20.0.0/16\", 8, 12)", "Carves a subnet out of a parent range: add 8 bits to the /16 prefix and take block 12, giving <code class=\"inline\">10.20.12.0/24</code>."),
            ("jsonencode({ ... })", "Serialises an HCL object to a JSON string, for user-data, IAM policies, or an output another tool reads."),
            ("terraform console", "Evaluates any of these interactively. Try <code class=\"inline\">cidrsubnet(\"10.0.0.0/16\", 8, 1)</code>."),
        ],
        lab=11,
    ),
    dict(
        eyebrow="Lab 12 &middot; Dynamic blocks",
        heading="dynamic: generate repeated nested blocks",
        concept=(
            "Some arguments are nested blocks rather than values &mdash; a security group's "
            "<code class=\"inline\">ingress</code> rules, for example. "
            "<code class=\"inline\">for_each</code> cannot help there, because it repeats whole "
            "resources. A <code class=\"inline\">dynamic</code> block repeats one nested block per "
            "collection entry, so adding a firewall rule becomes adding a map entry rather than "
            "editing HCL structure. Use it sparingly: a handful of literal blocks reads better."
        ),
        code=esc('''variable "ingress_rules" {
  type = map(object({
    port        = number
    cidr_blocks = list(string)
    description = string
  }))
  description = "One entry per inbound rule. No SSH rule: nothing in this lab connects to a host."
  default = {
    http  = { port = 80, cidr_blocks = ["10.0.0.0/8"], description = "internal HTTP" }
    https = { port = 443, cidr_blocks = ["10.0.0.0/8"], description = "internal HTTPS" }
  }
}

resource "aws_security_group" "service" {
  name_prefix = "lab12-dynamic-"
  description = "Ingress rules generated by a dynamic block"

  dynamic "ingress" {
    for_each = var.ingress_rules

    content {
      description = ingress.value.description
      from_port   = ingress.value.port
      to_port     = ingress.value.port
      protocol    = "tcp"
      cidr_blocks = ingress.value.cidr_blocks
    }
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "lab12-dynamic-sg", Lab = "lab12" }
}'''),
        rows=[
            ("dynamic \"ingress\"", "The label names the nested block type to generate. It must be a block the resource actually accepts."),
            ("for_each = var.ingress_rules", "One <code class=\"inline\">ingress</code> block per map entry. Two entries here means two rules."),
            ("content { ... }", "The template for each generated block. Everything inside is emitted once per iteration."),
            ("ingress.value.port", "Inside a dynamic block the iterator is named after the block, so it is <code class=\"inline\">ingress.value</code>, not <code class=\"inline\">each.value</code>."),
            ("from_port = to_port", "Both set to the same port, which is how a single-port rule is expressed."),
            ("egress stays literal", "There is only one egress rule, so a plain block is clearer than a generated one."),
            ("name_prefix", "Lets AWS append a unique suffix, so repeated applies cannot collide on a fixed group name."),
            ("no vpc_id", "This group is not placed in a VPC, so it is created in the region's default VPC. See the note below."),
            ("adding a rule", "Add a map entry, for example <code class=\"inline\">metrics = { port = 9100, ... }</code>. The resource body does not change."),
        ],
        lang_note=(
            "<strong>This lab needs a default VPC.</strong> An "
            "<code class=\"inline\">aws_security_group</code> with no "
            "<code class=\"inline\">vpc_id</code> is created in the region's default VPC, which a "
            "fresh training account may not have. <code class=\"inline\">terraform plan</code> "
            "does not detect it; the apply fails with "
            "<code class=\"inline\">VPCIdNotSpecified: No default VPC for this user</code>. Check "
            "with <code class=\"inline\">aws ec2 describe-vpcs --filters Name=isDefault,Values=true "
            "--query 'Vpcs[].VpcId' --output text</code>, and create one with "
            "<code class=\"inline\">aws ec2 create-default-vpc</code>. Lab 21 avoids this entirely "
            "by building its own VPC and setting <code class=\"inline\">vpc_id</code> explicitly."
        ),
        lab=12,
    ),
]

# ---------------------------------------------------------------------------
# Tier 3 — Advanced
# ---------------------------------------------------------------------------
ADVANCED_TOPICS = [
    dict(
        eyebrow="Lab 13 &middot; Providers",
        heading="Several providers in one configuration, and aliases",
        concept=(
            "One root module can configure any number of providers. Two different providers &mdash; "
            "AWS and <code class=\"inline\">random</code> &mdash; simply get one "
            "<code class=\"inline\">provider</code> block each. Two configurations of the "
            "<em>same</em> provider, such as two AWS regions, need an "
            "<code class=\"inline\">alias</code>, and every resource that should use the "
            "non-default one must say so with a <code class=\"inline\">provider</code> argument."
        ),
        code=esc('''terraform {
  required_providers {
    aws    = { source = "hashicorp/aws", version = "~> 5.0" }
    random = { source = "hashicorp/random", version = "~> 3.0" }
  }
}

provider "aws" {
  region = "us-east-1"
}

provider "aws" {
  alias  = "west"
  region = "us-west-2"
}

resource "random_pet" "label" {
  length = 2
}

resource "aws_s3_bucket" "west_logs" {
  provider = aws.west
  bucket   = "tf-labs-${random_pet.label.id}-west"

  tags = { Name = "west-logs", Lab = "lab13" }
}

output "composition" {
  value = {
    default_region = "us-east-1"
    label          = random_pet.label.id
    west_bucket    = aws_s3_bucket.west_logs.bucket
  }
}'''),
        rows=[
            ("two required_providers entries", "Each provider is a separate plugin download and a separate credential context."),
            ("first provider \"aws\"", "No alias, so this is the default. Any AWS resource that says nothing about providers uses it."),
            ("alias = \"west\"", "Names a second AWS configuration. Its address is <code class=\"inline\">aws.west</code>."),
            ("provider = aws.west", "Sends this one resource to the us-west-2 configuration. Without it the bucket would land in us-east-1."),
            ("bucket = \"tf-labs-${...}\"", "S3 bucket names are globally unique, so the random suffix keeps concurrent learners from colliding."),
            ("random_pet.label.id", "A cross-provider reference. Terraform orders the graph so the name exists before the bucket is created."),
        ],
        lab=13,
    ),
    dict(
        eyebrow="Lab 14 &middot; Provisioners",
        heading="local-exec: run a command on the machine running Terraform",
        concept=(
            "A <em>provisioner</em> runs a script as part of a resource's lifecycle, for things no "
            "provider expresses declaratively. <code class=\"inline\">local-exec</code> runs on "
            "your own machine or CI runner, not on the created resource, so no SSH is involved. "
            "HashiCorp calls provisioners a last resort and so should you: they are not "
            "idempotent, and their output ends up in logs. Prefer "
            "<code class=\"inline\">user_data</code> or a configuration-management tool."
        ),
        code=esc('''variable "message" {
  type        = string
  description = "Text the local command prints."
  default     = "local-exec completed"
}

resource "terraform_data" "local_action" {
  input = var.message

  provisioner "local-exec" {
    command = "printf '%s\\n' '${self.input}' >> provisioner.log"
  }

  provisioner "local-exec" {
    when    = destroy
    command = "printf 'destroyed\\n' >> provisioner.log"
  }
}

output "message" {
  value = terraform_data.local_action.output
}'''),
        rows=[
            ("resource \"terraform_data\"", "A built-in resource that stores a value and participates in the graph. It creates nothing in any cloud, so it is free to experiment with."),
            ("input = var.message", "Whatever is stored here becomes readable as <code class=\"inline\">.output</code> after apply."),
            ("provisioner \"local-exec\"", "Runs on the Terraform host after the resource is created. The default hook is create."),
            ("command = \"printf ...\"", "Executed through the local shell, so it depends on the operating system of whatever runs Terraform &mdash; a real portability hazard between laptop and CI."),
            ("self.input", "<code class=\"inline\">self</code> refers to the resource the provisioner is attached to. It is only valid inside a provisioner."),
            ("when = destroy", "Runs before the resource is destroyed instead of after creation. If it fails, the destroy is blocked."),
            ("failure behaviour", "A failed create-time provisioner marks the resource tainted, so the next apply destroys and recreates it."),
        ],
        lab=14,
    ),
    dict(
        eyebrow="Lab 15 &middot; Provisioners",
        heading="remote-exec: run commands on the host over SSH",
        concept=(
            "<code class=\"inline\">remote-exec</code> connects to the created machine and runs "
            "commands on it. That needs a <code class=\"inline\">connection</code> block giving "
            "the address, the user, and a private key, and it needs the host to be reachable and "
            "already accepting SSH &mdash; which makes it the most fragile thing in Terraform. In "
            "production, put the bootstrap script in "
            "<code class=\"inline\">user_data</code> instead, where the cloud runs it for you."
        ),
        code=esc('''variable "private_key_path" {
  type        = string
  description = "Path to the SSH private key for the target host."
  sensitive   = true
}

resource "terraform_data" "bootstrap" {
  input = var.host

  connection {
    type        = "ssh"
    host        = var.host
    user        = "ec2-user"
    private_key = file(pathexpand(var.private_key_path))
    timeout     = "2m"
  }

  provisioner "remote-exec" {
    inline = [
      "sudo dnf install -y httpd",
      "sudo systemctl enable --now httpd",
    ]
  }
}'''),
        rows=[
            ("sensitive = true", "Keeps the key path out of plan output. The key material itself must never be committed."),
            ("connection { type = \"ssh\" }", "How Terraform reaches the host. <code class=\"inline\">winrm</code> is the Windows equivalent."),
            ("host = var.host", "Target address. For a real instance this would be <code class=\"inline\">aws_instance.web.public_ip</code>."),
            ("user = \"ec2-user\"", "The default login user on Amazon Linux 2023. Ubuntu images use <code class=\"inline\">ubuntu</code>."),
            ("file(pathexpand(...))", "<code class=\"inline\">pathexpand</code> expands a leading <code class=\"inline\">~</code>; <code class=\"inline\">file</code> reads the key from disk at plan time."),
            ("timeout = \"2m\"", "How long to keep retrying the handshake while the instance finishes booting. Too short is the most common cause of failure here."),
            ("inline = [ ... ]", "A list of commands run in order on the host. A non-zero exit code fails the apply."),
            ("prefer user_data", "The same two commands in <code class=\"inline\">user_data</code> need no inbound SSH, no key on the Terraform host, and no reachability. Lab 21 does it that way."),
        ],
        lab=15,
    ),
    dict(
        eyebrow="Lab 16 &middot; Workspaces",
        heading="Workspaces: several states from one configuration",
        concept=(
            "A <em>workspace</em> is a named, separate state file for the same configuration "
            "directory. Every directory starts in the workspace called "
            "<code class=\"inline\">default</code>. Switching workspace switches which state "
            "Terraform reads, so <code class=\"inline\">dev</code> and "
            "<code class=\"inline\">staging</code> can coexist from identical code. Reference the "
            "current name as <code class=\"inline\">terraform.workspace</code> so resource names "
            "cannot collide in AWS."
        ),
        code=esc('''locals {
  environment = terraform.workspace
  name        = "labs-${terraform.workspace}"
}

resource "aws_vpc" "this" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name        = local.name
    Environment = local.environment
    Lab         = "lab16"
  }
}

output "workspace" {
  value = terraform.workspace
}

# terraform workspace list
# * default
# terraform workspace new dev
# terraform workspace select dev
# terraform apply
# terraform workspace show'''),
        rows=[
            ("terraform.workspace", "A built-in value holding the active workspace name. Available anywhere in the configuration, no variable needed."),
            ("name = \"labs-${terraform.workspace}\"", "Makes every AWS name workspace-specific, so applying in <code class=\"inline\">dev</code> and <code class=\"inline\">staging</code> does not produce duplicate names."),
            ("Environment tag", "Tags the environment from the same source of truth, so the console shows which workspace created a resource."),
            ("workspace new dev", "Creates the workspace and switches to it. Its state starts empty, so the first plan proposes creating everything."),
            ("workspace select dev", "Switches without creating. Always run <code class=\"inline\">workspace show</code> before an apply you care about."),
            ("workspace vs separate keys", "Workspaces share one backend key prefix and suit short-lived sandboxes. Production boundaries deserve wholly separate state keys, as in Lab 18."),
        ],
        lab=16,
    ),
    dict(
        eyebrow="Lab 17 &middot; Remote state",
        heading="An S3 backend puts state where the team can reach it",
        concept=(
            "A <em>backend</em> is where Terraform keeps state. The default is a local file, which "
            "no colleague and no CI job can read. The <code class=\"inline\">s3</code> backend "
            "stores it in a bucket instead, making it the shared system of record. Backend "
            "settings cannot use variables, so supply bucket and key at init time from a "
            "<code class=\"inline\">-backend-config</code> file rather than hardcoding a real "
            "bucket name in git. The backend locks the state itself: "
            "<code class=\"inline\">use_lockfile = true</code> makes Terraform write a "
            "<code class=\"inline\">.tflock</code> object beside the state object for the duration "
            "of an operation, so no second table and no second service are involved."
        ),
        code=esc('''terraform {
  # Higher than the track's >= 1.5.0 floor: backend.hcl.example sets use_lockfile,
  # which is experimental in 1.10 and generally available from 1.11.
  required_version = ">= 1.11.0"
  backend "s3" {}
}

# backend.hcl.example -> copy to backend.hcl and fill in
# bucket       = "replace-with-your-globally-unique-state-bucket"
# key          = "labs/lab17/terraform.tfstate"
# region       = "us-east-1"
# encrypt      = true
# use_lockfile = true

# terraform init -backend-config=backend.hcl'''),
        rows=[
            ("required_version = \"&gt;= 1.11.0\"", "Higher than the track floor of 1.5.0. <code class=\"inline\">use_lockfile</code> is experimental in 1.10 and generally available from 1.11; on 1.5&ndash;1.9 the backend rejects the argument at <code class=\"inline\">init</code>."),
            ("backend \"s3\" {}", "Selects the S3 backend and deliberately leaves it empty, a pattern called partial configuration."),
            ("bucket", "The S3 bucket holding state. Enable versioning on it so a bad apply can be rolled back."),
            ("key", "Path of the state object inside the bucket. This is the single most important field: two configurations sharing a key overwrite each other."),
            ("region", "Region of the bucket. Independent of the region your resources are created in."),
            ("encrypt = true", "Server-side encryption for the state object. State contains sensitive values in plain text, so this is not optional in practice."),
            ("use_lockfile = true", "Native S3 state locking, covered in Lab 18. Terraform writes <code class=\"inline\">&lt;key&gt;.tflock</code> next to the state object while an operation runs. Without it two simultaneous applies can corrupt state."),
            ("-backend-config=backend.hcl", "Feeds those settings to <code class=\"inline\">init</code>. Commit only the <code class=\"inline\">.example</code> file."),
        ],
        lang_note=(
            "Pre-1.11 material pairs the S3 backend with "
            "<code class=\"inline\">dynamodb_table</code> and a separate lock table. That argument "
            "is deprecated: Terraform 1.14 reports "
            "<code class=\"inline\">The parameter \"dynamodb_table\" is deprecated. Use parameter "
            "\"use_lockfile\" instead.</code> Recognise it in older code and blogs; do not write it "
            "in new configuration."
        ),
        lab=17,
    ),
    dict(
        eyebrow="Lab 18 &middot; Keys and locking",
        heading="State keys partition environments; locking serialises writes",
        concept=(
            "The backend <code class=\"inline\">key</code> is what separates one state from "
            "another inside a bucket, so a deliberate naming convention "
            "(<code class=\"inline\">{env}/{component}/terraform.tfstate</code>) is what keeps "
            "<code class=\"inline\">dev</code> from overwriting "
            "<code class=\"inline\">prod</code>. <em>Locking</em> solves a different problem: two "
            "people applying at once. With <code class=\"inline\">use_lockfile = true</code> the S3 "
            "backend locks natively &mdash; Terraform puts a small "
            "<code class=\"inline\">&lt;key&gt;.tflock</code> object next to the state object for "
            "the duration of the operation, and the second apply fails to acquire it rather than "
            "racing. This requires Terraform &gt;= 1.11.0, which is why labs 17&ndash;19 raise "
            "<code class=\"inline\">required_version</code> above the track floor."
        ),
        code=esc('''terraform {
  # Higher than the track's >= 1.5.0 floor: backend.hcl.example sets use_lockfile,
  # which is experimental in 1.10 and generally available from 1.11.
  required_version = ">= 1.11.0"
  backend "s3" {}
}

variable "environment" {
  type        = string
  default     = "dev"
  description = "Environment segment of the state key, e.g. dev or staging."
}

variable "component" {
  type        = string
  default     = "network"
  description = "Component segment of the state key, e.g. network or app."
}

locals {
  recommended_key = "labs/${var.environment}/${var.component}/terraform.tfstate"
}

resource "terraform_data" "key_design" {
  input = local.recommended_key
}

resource "terraform_data" "locking_note" {
  input = "S3 lockfiles prevent concurrent state writes."
}

output "recommended_state_key" {
  value = terraform_data.key_design.output
}

output "locking_note" {
  value = terraform_data.locking_note.output
}

# backend.hcl -> the key and the lock both live here, not in the .tf files
# key          = "labs/dev/network/terraform.tfstate"
# encrypt      = true
# use_lockfile = true

# A second apply while the first holds the lock:
# Error: Error acquiring the state lock
#
# Lock Info:
#   ID:        6a4e9f7c-...
#   Path:      tfstate-yourname-4821/labs/dev/network/terraform.tfstate
#   Operation: OperationTypeApply
#   Who:       you@your-host
#
# terraform force-unlock 6a4e9f7c-...   # only when the holder is definitely dead'''),
        rows=[
            ("required_version = \"&gt;= 1.11.0\"", "<code class=\"inline\">use_lockfile</code> is experimental in 1.10 and generally available from 1.11. A learner on 1.5&ndash;1.9 passes the track's own floor and then fails at <code class=\"inline\">terraform init</code>."),
            ("locals.recommended_key", "Computes the convention rather than describing it in a comment, so the naming rule is executable and reviewable."),
            ("labs/${var.environment}/${var.component}/...", "Environment then component. Changing either variable yields a completely separate state path."),
            ("output recommended_state_key", "Prints the value you then paste into <code class=\"inline\">backend.hcl</code>, which is where the key actually takes effect. The output is advice; it does not move state."),
            ("use_lockfile = true", "Native S3 locking. Terraform creates <code class=\"inline\">labs/dev/network/terraform.tfstate.tflock</code> on acquire and deletes it on release. No DynamoDB table, no extra IAM, no extra cost."),
            ("Error acquiring the state lock", "The expected, healthy outcome of a concurrent apply. Terraform refused to write rather than racing."),
            ("Path / Who / Operation", "Lock metadata naming the state key, who holds it and what they are doing. Usually enough to resolve it with a message rather than a command."),
            ("force-unlock ID", "Deletes the <code class=\"inline\">.tflock</code> object by hand. Emergency only &mdash; running it while the other apply is alive is how state actually gets corrupted."),
        ],
        lang_note=(
            "Before Terraform 1.11 the S3 backend had no native lock, so the standard answer was a "
            "<code class=\"inline\">dynamodb_table</code> argument pointing at a DynamoDB table "
            "with a <code class=\"inline\">LockID</code> string partition key. You will meet that "
            "in older repositories and tutorials. It is now deprecated &mdash; Terraform 1.14 "
            "emits <code class=\"inline\">The parameter \"dynamodb_table\" is deprecated. Use "
            "parameter \"use_lockfile\" instead.</code> Use "
            "<code class=\"inline\">use_lockfile</code> in anything you write."
        ),
        lab=18,
    ),
    dict(
        eyebrow="Lab 19 &middot; Migration",
        heading="Moving existing local state into a remote backend",
        concept=(
            "Adding a <code class=\"inline\">backend</code> block to a directory that already has "
            "a local <code class=\"inline\">terraform.tfstate</code> does not move anything by "
            "itself. <code class=\"inline\">terraform init -migrate-state</code> copies the "
            "existing state into the new backend and asks for confirmation first. The resources "
            "are untouched throughout: this is purely a move of the bookkeeping, and the proof it "
            "worked is a plan that reports no changes."
        ),
        code=esc('''cp terraform.tfstate pre-migration.tfstate.backup

terraform init -migrate-state -backend-config=backend.hcl
# Initializing the backend...
# Do you want to copy existing state to the new backend?
#   Pre-existing state was found while migrating the previous "local" backend
#   to the newly configured "s3" backend. Do you want to copy this state?
#
#   Enter a value: yes

terraform state list
terraform plan
# No changes. Your infrastructure matches the configuration.

terraform state pull > remote-copy.tfstate'''),
        rows=[
            ("cp terraform.tfstate ...", "Take your own backup first. Migration is the one moment where a mistake loses the map between code and real infrastructure."),
            ("init -migrate-state", "Tells Terraform the backend changed on purpose and that the existing state should be carried across."),
            ("-backend-config=backend.hcl", "Supplies the bucket and key for the destination, the same file Lab 17 introduced."),
            ("Enter a value: yes", "The confirmation prompt. Answering no leaves the local state in place and the remote backend empty."),
            ("terraform state list", "First check after migration: the same addresses must be present as before."),
            ("terraform plan", "Second check, and the real one. No changes means the migrated state still matches reality, so nothing will be recreated."),
            ("terraform state pull", "Fetches the state from the backend to stdout. Use it for backups; never edit and push it by hand."),
        ],
        lab=19,
    ),
    dict(
        eyebrow="Lab 20 &middot; Composition",
        heading="Reading another configuration's outputs",
        concept=(
            "Once state is remote, one configuration can read another's outputs with the "
            "<code class=\"inline\">terraform_remote_state</code> data source. A network team "
            "publishes <code class=\"inline\">vpc_id</code> and "
            "<code class=\"inline\">subnet_id</code>; application teams consume them read-only "
            "instead of duplicating the VPC code or pasting IDs into tfvars. Only declared "
            "outputs are visible &mdash; the producer's internal resources stay private."
        ),
        code=esc('''data "terraform_remote_state" "network" {
  backend = "s3"

  config = {
    bucket = "myorg-terraform-state"
    key    = "labs/dev/network/terraform.tfstate"
    region = "us-east-1"
  }
}

resource "aws_instance" "app" {
  ami           = data.aws_ami.al2023.id
  instance_type = "t3.micro"
  subnet_id     = data.terraform_remote_state.network.outputs.subnet_id

  tags = { Name = "app", Lab = "lab20" }
}'''),
        rows=[
            ("data \"terraform_remote_state\"", "Reads a state file belonging to another root module. It is a data source, so this configuration can never modify what it reads."),
            ("backend = \"s3\"", "Which backend type to read. It must match the backend the producer actually writes to."),
            ("config = { ... }", "Where that state lives. The bucket, key, and region identify the producer's state object exactly."),
            ("key = \"labs/dev/network/...\"", "Points at the network state specifically. Pointing at the wrong environment's key is the classic way to attach production subnets to a dev instance."),
            (".outputs.subnet_id", "Only values the producer declared as <code class=\"inline\">output</code> appear under <code class=\"inline\">.outputs</code>. Undeclared internals are unreachable."),
            ("read permissions", "The consumer needs S3 read access to that key. Read-only is enough and is what it should be granted."),
        ],
        lab=20,
    ),
    dict(
        eyebrow="Lab 21 &middot; Capstone",
        heading="The whole picture: VPC, IGW, route table, subnet, SG, EC2",
        concept=(
            "The capstone builds a working public web server from nothing. An "
            "<em>internet gateway</em> attaches the VPC to the internet; a <em>route table</em> "
            "with a default route to that gateway is what makes a subnet <em>public</em>; the "
            "security group opens port 80; and <code class=\"inline\">user_data</code> "
            "installs a web server on first boot. The output is a URL you can actually open, "
            "which is the payoff for the entire track."
        ),
        code=esc('''data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "this" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true

  tags = merge(local.common_tags, { Name = local.name })
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(local.common_tags, { Name = "${local.name}-igw" })
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, { Name = "${local.name}-public" })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = merge(local.common_tags, { Name = "${local.name}-public-rt" })
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = "t3.micro"
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = <<-EOT
    #!/bin/bash
    dnf install -y httpd
    systemctl enable --now httpd
    echo "<h1>${local.name} is live</h1>" > /var/www/html/index.html
  EOT

  tags = merge(local.common_tags, { Name = "${local.name}-web" })
}

output "web_url" {
  value = "http://${aws_instance.web.public_ip}"
}'''),
        rows=[
            ("aws_vpc, cidr_block", "The private network, with room for 65,536 addresses. Every other resource here lives inside it."),
            ("enable_dns_hostnames", "Gives instances public DNS names as well as IPs. Required before public hostnames resolve."),
            ("aws_internet_gateway", "Attaches the VPC to the internet. On its own it routes nothing."),
            ("data.aws_availability_zones", "Asks the account which zones it can actually use. Zone names are mapped per account, so a hardcoded <code class=\"inline\">us-east-1a</code> is not the same hardware everywhere and may not exist or have capacity in yours."),
            ("names[0]", "Takes the first usable zone. The subnet is zonal, so it must name exactly one."),
            ("map_public_ip_on_launch", "Instances launched in this subnet get a public IP automatically."),
            ("route { 0.0.0.0/0 }", "The default route: any destination not inside the VPC goes to the gateway. This line is what makes the subnet public."),
            ("aws_route_table_association", "Binds the route table to the subnet. Skip it and the subnet silently keeps the VPC's main table and stays private."),
            ("subnet_id on the instance", "Places the instance in the public subnet. Combined with the route and the public IP, the server becomes reachable."),
            ("user_data = &lt;&lt;-EOT", "A heredoc script the cloud runs once on first boot. <code class=\"inline\">&lt;&lt;-</code> strips the leading indentation."),
            ("dnf install -y httpd", "Amazon Linux 2023 uses <code class=\"inline\">dnf</code>. Running it here needs no SSH and no provisioner."),
            ("output web_url", "Builds the browsable URL from the assigned public IP. This is the observable proof the whole stack works."),
        ],
        lang_note="This lab bills for real. Run <code class=\"inline\">terraform destroy</code> as soon "
                  "as you have loaded the page.",
        lab=21,
    ),
]


def render_tier(tier: str, topics: list[dict]) -> str:
    meta = TIERS[tier]
    tier_labs = [lab for lab in LABS if lab[3] == tier]
    intro = f"""        <div class="card">
            <span class="eyebrow">Tier {"123"[list(TIERS).index(tier)]} &middot; {meta["range"]}</span>
            <h2>{meta["label"]} Terraform</h2>
            <p class="concept">{meta["blurb"]}</p>
            <table>
                <thead><tr><th style="width:9%;">Lab</th><th style="width:30%;">Title</th><th>Topic</th></tr></thead>
                <tbody>
"""
    for num, slug, title, _tier, topic_text in tier_labs:
        intro += (f'                <tr><td class="lineref">lab{num:02d}</td>'
                  f'<td><a href="../labmanuals/{slug}.md">{title}</a></td>'
                  f"<td>{topic_text}</td></tr>\n")
    intro += """                </tbody>
            </table>
            <div class="note">Starting from zero? Read
                <a href="terraform-101.html">Terraform 101</a> first &mdash; what Terraform is,
                HCL, providers, version constraints, state, and drift &mdash; then the
                <a href="aws-primer.html">AWS primer</a> for regions, VPCs, subnets, gateways,
                and security groups.</div>
        </div>
"""

    sections = [intro]
    for spec in topics:
        href, label = practises(spec["lab"])
        sections.append(topic(
            spec["eyebrow"], spec["heading"], spec["concept"], spec["code"],
            spec["rows"], href, label, lang_note=spec.get("lang_note", ""),
        ))

    stats = [f"{len(tier_labs)} labs", meta["range"], TF_FLOOR, AWS_PIN, "Region us-east-1"]
    return page(
        f"Terraform &mdash; {meta['label']} Concepts",
        f"{len(topics)} topics. Each one: what it is, a real example, every significant line "
        "explained, and the lab that practises it.",
        "".join(sections),
        active=tier,
        stats=stats,
    )


INDEX_CSS = """
.search-bar { margin: 4px 0 14px; }
.search-bar input {
    width: 100%; max-width: 480px; padding: 10px 14px; font-family: inherit;
    font-size: 0.92rem; color: var(--slate-900); background: #f8fafc;
    border: 1px solid var(--slate-200); border-radius: 10px; outline: none;
}
.search-bar input:focus { border-color: var(--blue); box-shadow: 0 0 0 3px rgba(37,99,235,0.12); }
.tiergrid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px;
            margin-bottom: 18px; }
.tiercard {
    background: #fff; border: 1px solid var(--slate-200); border-radius: 14px;
    padding: 16px 18px; box-shadow: 0 2px 12px rgba(15, 23, 42, 0.05);
}
.tiercard h2 { font-size: 1.05rem; margin: 6px 0 4px; }
.tiercard p { color: var(--slate-700); font-size: 0.88rem; margin-bottom: 8px; }
.tiercard .range { display: block; color: var(--slate-500); font-size: 0.78rem;
                   font-family: "SF Mono", Menlo, monospace; margin-bottom: 8px; }
/* entry-point sequence: Terraform 101 -> AWS primer -> lab00 */
.startcard {
    background: #fff; border: 2px solid var(--blue); border-radius: 14px;
    padding: 18px 20px; margin-bottom: 18px; box-shadow: 0 4px 16px rgba(37, 99, 235, 0.10);
}
.seq { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px;
       margin-top: 12px; }
.seq > div {
    position: relative; padding: 14px 16px 14px 18px; border-radius: 12px;
    border: 1px solid var(--slate-200); background: linear-gradient(180deg, #fff, #f8fbff);
}
.seq > div.first { border-color: var(--blue); background: #eff6ff; }
.seq .step {
    display: inline-block; width: 22px; height: 22px; line-height: 22px; text-align: center;
    border-radius: 999px; background: var(--blue); color: #fff; font-size: 0.74rem;
    font-weight: 800; margin-bottom: 6px;
}
.seq h3 { margin: 0 0 4px; font-size: 1rem; }
.seq h3 a { color: var(--blue); text-decoration: none; }
.seq h3 a:hover { text-decoration: underline; }
.seq p { color: var(--slate-700); font-size: 0.86rem; }
.seq .q { display: block; color: var(--slate-500); font-size: 0.78rem; font-style: italic;
          margin-top: 6px; }
.arrow { color: var(--slate-500); font-weight: 800; }
.no-results { display: none; padding: 14px; color: var(--slate-500); font-size: 0.9rem; }
@media (max-width: 768px) { .tiergrid { grid-template-columns: 1fr; } }
"""

INDEX_JS = """        <script>
        (function () {
            var box = document.getElementById('lab-search');
            var rows = document.querySelectorAll('#lab-table tbody tr');
            var empty = document.getElementById('no-results');
            if (!box) { return; }
            box.addEventListener('input', function () {
                var q = box.value.toLowerCase().trim();
                var shown = 0;
                for (var i = 0; i < rows.length; i++) {
                    var hit = !q || rows[i].textContent.toLowerCase().indexOf(q) !== -1;
                    rows[i].style.display = hit ? '' : 'none';
                    if (hit) { shown++; }
                }
                empty.style.display = shown ? 'none' : 'block';
            });
        })();
        </script>
"""


def render_index() -> str:
    cards = []
    for key, meta in TIERS.items():
        count = len([lab for lab in LABS if lab[3] == key])
        cards.append(f"""            <div class="tiercard">
                <span class="tag {key}">{meta["label"]}</span>
                <h2><a class="backlink" href="{key}.html">{meta["label"]} &rarr;</a></h2>
                <span class="range">{meta["range"]} &middot; {count} labs</span>
                <p>{meta["blurb"]}</p>
            </div>""")

    rows = []
    for num, slug, title, tier, topic_text in LABS:
        rows.append(
            f'                    <tr>'
            f'<td class="lineref">lab{num:02d}</td>'
            f'<td><a href="../labmanuals/{slug}.md">{title}</a></td>'
            f'<td><span class="tag {tier}">{TIERS[tier]["label"]}</span></td>'
            f"<td>{topic_text}</td>"
            f'<td><a href="{tier}.html">{TIERS[tier]["label"]} concepts</a></td>'
            f"</tr>"
        )

    lab00_href, _ = practises(0)
    body = f"""        <div class="startcard">
            <span class="tag basic">Start here</span>
            <h2>Never used Terraform before? Read these two pages first, in this order</h2>
            <p class="concept">Both primers assume you know nothing. The first explains the tool,
                the second explains the cloud it will be talking to. Together they take about
                forty minutes, and they are the difference between following lab00 and
                understanding it.</p>
            <div class="seq">
                <div class="first">
                    <span class="step">1</span>
                    <h3><a href="terraform-101.html">Terraform 101 &rarr;</a></h3>
                    <p>What Terraform is and who owns it, what HCL is and the anatomy of a block,
                        what a provider is and how to add one, every version-constraint operator
                        including <code class="inline">~&gt;</code>, the CLI commands and the plan
                        symbols, what state is, and what drift means.</p>
                    <span class="q">Answers: what am I actually running?</span>
                </div>
                <div>
                    <span class="step">2</span>
                    <h3><a href="aws-primer.html">AWS Primer &rarr;</a></h3>
                    <p>Region and availability zone, VPC and CIDR, public and private subnets,
                        internet gateway, route table, security group, EC2 instance, key pair, and
                        IAM access keys &mdash; each with its Terraform resource type, plus the
                        diagram of what Lab 21 builds.</p>
                    <span class="q">Answers: what is a VPC?</span>
                </div>
                <div>
                    <span class="step">3</span>
                    <h3><a href="{lab00_href}">Lab 00 &rarr;</a></h3>
                    <p>Now start typing. Verify your Terraform and AWS CLI versions, export your
                        access keys, write your first provider block, and run
                        <code class="inline">terraform init</code>. Creates nothing billable.</p>
                    <span class="q">Answers: does my setup work?</span>
                </div>
            </div>
            <div class="note">Already comfortable with Terraform and AWS? Skip straight to the
                <a href="basic.html">Basic tier concepts</a> or to
                <a href="{lab00_href}">Lab 00</a>.</div>
        </div>

        <div class="tiergrid">
{chr(10).join(cards)}
        </div>

        <div class="card">
            <span class="eyebrow">All {len(LABS)} labs</span>
            <h2>Lab sequence</h2>
            <p class="concept">Work through them in order: each lab assumes the one before it.
                Every manual links to its runnable code under
                <code class="inline">terraform/labs/</code>.</p>
            <div class="search-bar">
                <input type="text" id="lab-search" autocomplete="off"
                       placeholder="Filter labs, e.g. state, modules, for_each, backend...">
            </div>
            <table id="lab-table">
                <thead><tr>
                    <th style="width:8%;">Lab</th>
                    <th style="width:24%;">Manual</th>
                    <th style="width:12%;">Tier</th>
                    <th>Topic</th>
                    <th style="width:16%;">Concepts</th>
                </tr></thead>
                <tbody>
{chr(10).join(rows)}
                </tbody>
            </table>
            <div class="no-results" id="no-results">No labs match that filter.</div>
        </div>

        <div class="card">
            <span class="eyebrow">All {len(HTML_PAGES)} pages</span>
            <h2>The HTML set</h2>
            <p class="concept">Six self-contained pages. No CDN, no external fonts, no build step
                &mdash; open any of them offline, or print them.</p>
            <table>
                <thead><tr><th style="width:22%;">Page</th><th style="width:14%;">Read it</th><th>Contents</th></tr></thead>
                <tbody>
                <tr><td class="lineref"><a href="terraform-101.html">terraform-101.html</a></td><td><strong>1st</strong></td><td>Terraform fundamentals from absolute zero: the tool, HCL, providers, version constraints, the CLI, state, drift.</td></tr>
                <tr><td class="lineref"><a href="aws-primer.html">aws-primer.html</a></td><td><strong>2nd</strong></td><td>AWS concepts from absolute zero, each with its Terraform resource type, plus the capstone architecture diagram.</td></tr>
                <tr><td class="lineref">index.html</td><td>as needed</td><td>This page: the entry-point sequence, the tier cards, and the searchable table of all {len(LABS)} labs.</td></tr>
                <tr><td class="lineref"><a href="basic.html">basic.html</a></td><td>with lab00&ndash;05</td><td>Tier 1 concepts.</td></tr>
                <tr><td class="lineref"><a href="intermediate.html">intermediate.html</a></td><td>with lab06&ndash;12</td><td>Tier 2 concepts.</td></tr>
                <tr><td class="lineref"><a href="advanced.html">advanced.html</a></td><td>with lab13&ndash;21</td><td>Tier 3 concepts.</td></tr>
                </tbody>
            </table>
        </div>

        <div class="card">
            <span class="eyebrow">How to use this track</span>
            <h2>Read, then do, then run</h2>
            <table>
                <thead><tr><th style="width:26%;">Where</th><th>What it is for</th></tr></thead>
                <tbody>
                <tr><td class="lineref">html/</td><td>The {len(HTML_PAGES)} pages above. Concept, example, line-by-line explanation, and a link to the matching lab.</td></tr>
                <tr><td class="lineref">labmanuals/</td><td>The step-by-step manual you follow at the keyboard, with expected output after every command.</td></tr>
                <tr><td class="lineref">labs/</td><td>The runnable <code class="inline">.tf</code> code, one root module per lab. Edit files here rather than pasting from the manual.</td></tr>
                <tr><td class="lineref">docs/</td><td>Longer written deep dives per tier, for after the lab.</td></tr>
                </tbody>
            </table>
            <div class="warn">Every AWS lab costs money while it is running. Finish with
                <code class="inline">terraform destroy</code>, every time.</div>
        </div>
{INDEX_JS}"""

    return page(
        "Terraform Track",
        f"{len(LABS)} labs across three tiers &mdash; from your first "
        "<code class=\"inline\">terraform init</code> to a working public web server built "
        "entirely in code.",
        body,
        active="index",
        stats=[f"{len(LABS)} labs", "3 tiers", f"{len(HTML_PAGES)} HTML pages", TF_FLOOR,
               AWS_PIN, "Region us-east-1", "Offline"],
        extra_css=INDEX_CSS,
    )


def write(name: str, content: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")
    print(f"  {len(content.splitlines()):5d} lines  {path.relative_to(ROOT)}")


def check_hrefs() -> int:
    """Every ../labmanuals/labNN-*.md href must resolve to a real file."""
    missing = []
    for num, slug, _title, _tier, _topic in LABS:
        target = ROOT / "terraform" / "labmanuals" / f"{slug}.md"
        if not target.exists():
            missing.append(f"lab{num:02d}: {target.relative_to(ROOT)}")
    if missing:
        print("\nMISSING lab manuals referenced by generated hrefs:")
        for item in missing:
            print(f"  {item}")
    else:
        print(f"\nhref check: all {len(LABS)} lab manual targets exist.")
    return len(missing)


def check_page_set() -> int:
    """No generated page may link to a Terraform HTML page outside the six-page set."""
    import re

    bad = 0
    for name in ("index.html", "basic.html", "intermediate.html", "advanced.html"):
        text = (OUT_DIR / name).read_text(encoding="utf-8")
        for href in re.findall(r'href="\.?/?([a-z0-9._-]+\.html)"', text):
            if href not in HTML_PAGES:
                print(f"  OFF-SET LINK {name} -> {href}")
                bad += 1
            elif not (OUT_DIR / href).exists():
                print(f"  MISSING PAGE {name} -> {href}")
                bad += 1
    if not bad:
        print(f"page-set check: every HTML link stays inside the {len(HTML_PAGES)}-page set "
              "and resolves on disk.")
    return bad


def main() -> None:
    print("Generating Terraform track HTML:")
    write("index.html", render_index())
    write("basic.html", render_tier("basic", BASIC_TOPICS))
    write("intermediate.html", render_tier("intermediate", INTERMEDIATE_TOPICS))
    write("advanced.html", render_tier("advanced", ADVANCED_TOPICS))
    check_hrefs()
    check_page_set()


if __name__ == "__main__":
    main()
