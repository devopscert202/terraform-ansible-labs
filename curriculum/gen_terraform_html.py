#!/usr/bin/env python3
"""Generate the Terraform track HTML: the index and the single concepts page.

Output (all under terraform/html/):
    index.html          track catalog: entry-point sequence, 25-lab table, search
    concepts.html       every topic, lab00 to lab24, in one continuous sequence

There is no tier-based navigation and no tier page. Tier is a per-lab label in the
index catalog table only. The other two pages in the four-page set are generated
elsewhere and are only linked from here: terraform-101.html by gen_terraform_101.py,
aws-primer.html by gen_aws_primer.py.

Every topic section follows the mandated four-part flow via tf_style.topic():
concept overview -> example code block -> line-by-line explanation -> lab link.
Each card carries a stable anchor id so the sticky topic nav can jump to it.

Re-runnable: each run overwrites its two files with byte-identical output for
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

# The complete Terraform HTML page set. index and concepts are written by this script;
# terraform-101 and aws-primer are written by their own generators. No other Terraform
# HTML page exists, so nothing here may link outside this set.
HTML_PAGES = [
    "index.html",
    "terraform-101.html",
    "aws-primer.html",
    "concepts.html",
]

# Written by this script; the other two are checked for existence only.
OWNED_PAGES = ["index.html", "concepts.html"]

# ---------------------------------------------------------------------------
# Locked 25-lab sequence (lab00-lab24). num, slug, title, tier, topic
#
# Tier split applied everywhere in this repository:
#   Basic        lab00-lab05   6 labs
#   Intermediate lab06-lab12   7 labs, including the capstone at lab10
#   Advanced     lab13-lab24  12 labs
# The capstone sits mid-track at lab10 so the learner builds something end to end
# before the tooling-heavy Advanced tier. Dynamic blocks sit at lab21, immediately
# before the two S3 labs that close the track.
# ---------------------------------------------------------------------------
LABS = [
    (0, "lab00-aws-setup-and-init", "AWS Setup and First Init", "basic",
     "Credentials, provider block, first init"),
    (1, "lab01-providers-init", "Providers and Initialization", "basic",
     "required_providers, lock file, validate"),
    (2, "lab02-console-vpc", "Building a Network by Hand in the Console", "basic",
     "Manual console build, contrasted with IaC"),
    (3, "lab03-first-ec2", "Your First EC2 Instance", "basic",
     "VPC, two subnets, security group, instance"),
    (4, "lab04-plan-apply-destroy", "Plan, Apply, and Destroy", "basic",
     "The core workflow on a real VPC, no cloud cost"),
    (5, "lab05-fmt-validate", "Format and Validate", "basic",
     "fmt, validate, CI-style quality gates"),
    (6, "lab06-variables-outputs", "Variables and Outputs", "intermediate",
     "Typed inputs, locals, outputs, own VPC"),
    (7, "lab07-tfvars-secrets", "tfvars and Secrets", "intermediate",
     "tfvars files, precedence, sensitive, values as VPC tags"),
    (8, "lab08-local-state", "Local State", "intermediate",
     "terraform.tfstate, a real VPC ID in state, drift"),
    (9, "lab09-modules", "Modules", "intermediate",
     "Child modules, inputs, outputs"),
    (10, "lab10-capstone-vpc-ec2", "Capstone: VPC to public web server", "intermediate",
     "VPC, IGW, subnet, route table, SG, EC2"),
    (11, "lab11-collections", "Collections", "intermediate",
     "list vs set vs map, for expressions, a subnet from a map key"),
    (12, "lab12-functions", "Functions", "intermediate",
     "String, collection, CIDR, encoding, cidrsubnet() as a real subnet"),
    (13, "lab13-multi-provider", "Multi-provider configuration", "advanced",
     "Two providers, provider aliases"),
    (14, "lab14-local-exec-provisioner", "local-exec provisioner", "advanced",
     "Run a command on the Terraform host"),
    (15, "lab15-remote-exec-provisioner", "remote-exec provisioner", "advanced",
     "SSH connection block, inline commands"),
    (16, "lab16-workspaces", "Workspaces", "advanced",
     "terraform.workspace, one real VPC per workspace"),
    (17, "lab17-s3-backend", "S3 backend", "advanced",
     "Remote state in S3, backend config files"),
    (18, "lab18-state-keys-locking", "State keys and locking", "advanced",
     "Key conventions, S3 native lockfile"),
    (19, "lab19-state-migration", "State migration", "advanced",
     "init -migrate-state, backups, a real VPC that must not move"),
    (20, "lab20-remote-state-consumer", "Remote state consumer", "advanced",
     "terraform_remote_state data source"),
    (21, "lab21-dynamic-blocks", "Dynamic Blocks", "advanced",
     "Generated nested blocks from data"),
    (22, "lab22-ec2-s3-backend", "EC2 with remote state in S3", "advanced",
     "The capstone build, state kept in S3"),
    (23, "lab23-s3-bucket", "S3 bucket as a Terraform resource", "advanced",
     "aws_s3_bucket, versioning, encryption"),
    (24, "lab24-count-foreach-buckets", "count and for_each on real buckets", "advanced",
     "count by position vs for_each by name"),
]

# Tier survives only as a per-lab label in the index catalog table: it tells a learner how
# much a lab assumes. It is not a page, a nav item, or a grouping anywhere in the HTML.
TIERS = {
    "basic": {"label": "Basic", "range": "lab00-lab05"},
    "intermediate": {"label": "Intermediate", "range": "lab06-lab12"},
    "advanced": {"label": "Advanced", "range": "lab13-lab24"},
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
# All 26 topic cards, lab00 to lab24, one continuous sequence.
#
# There is no tier grouping here and no per-tier page: a learner reads straight
# down concepts.html, or jumps with the sticky topic nav. The capstone (lab10) and
# dynamic blocks (lab21) sit at their sequence positions like every other topic —
# neither needs the out-of-order injection hook the tier pages used to require.
#
# Order in this list IS the order on the page. Keep it ascending by "lab".
# ---------------------------------------------------------------------------
TOPICS = [
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
  region = "us-east-2"
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
export AWS_DEFAULT_REGION="us-east-2"

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
  region = "us-east-2"
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
        lang_note="This lab has no <code class=\"inline\">.tf</code> files. Lab 10 builds the same "
                  "network in code, and the difference in reviewability and repeatability is the "
                  "whole point of the exercise.",
        lab=2,
    ),
    dict(
        eyebrow="Lab 03 &middot; Resources",
        heading="Resources, data sources, and your first EC2 instance in its own network",
        concept=(
            "A <em>resource</em> is an object Terraform owns: it creates it, records its ID in "
            "state, updates it, and destroys it. A <em>data source</em> is a read-only query "
            "against something that already exists. An <em>AMI</em> (Amazon Machine Image) is the "
            "disk image an EC2 instance boots from, and its ID differs per region, so resolve it "
            "with <code class=\"inline\">data \"aws_ami\"</code> instead of hardcoding an ID. This "
            "lab builds the network it needs &mdash; a VPC, two subnets, and a security group "
            "&mdash; and launches the instance into it, so the configuration states where the "
            "instance lands instead of inheriting whatever the account happens to have."
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

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr           # 10.0.0.0/16
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = { Name = "${var.instance_name}-vpc", Lab = "lab03", ManagedBy = "Terraform" }
}

resource "aws_subnet" "public" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.public_subnet_cidr    # 10.0.1.0/24
  availability_zone = var.public_subnet_az      # us-east-2a

  tags = { Name = "${var.instance_name}-public", Lab = "lab03", ManagedBy = "Terraform" }
}

resource "aws_subnet" "private" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.private_subnet_cidr   # 10.0.2.0/24
  availability_zone = var.private_subnet_az     # us-east-2b

  tags = { Name = "${var.instance_name}-private", Lab = "lab03", ManagedBy = "Terraform" }
}

resource "aws_security_group" "instance" {
  name        = "${var.instance_name}-sg"
  description = "SSH from inside the VPC only, all outbound"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH from within the VPC"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.instance_name}-sg", Lab = "lab03", ManagedBy = "Terraform" }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.instance.id]

  tags = { Name = var.instance_name, Lab = "lab03", ManagedBy = "Terraform" }
}'''),
        rows=[
            ("data \"aws_ami\" \"amazon_linux\"", "Asks EC2 for a matching image at plan time. Nothing is created and nothing enters state as a managed object."),
            ("most_recent = true", "Several images match the filter; take the newest published one."),
            ("owners = [\"amazon\"]", "Restricts the search to images published by AWS itself, so a look-alike community AMI cannot be selected."),
            ("filter { name = \"name\" }", "Matches the Amazon Linux 2023 x86_64 naming pattern. The <code class=\"inline\">*</code> absorbs the date portion of the name."),
            ("filter { virtualization-type }", "Restricts to HVM images, the only virtualization type current instance families support."),
            ("aws_vpc.main", "The private network this lab creates for itself, a <code class=\"inline\">/16</code> with room for 65,536 addresses. Every other resource here lives inside it."),
            ("enable_dns_hostnames / _support", "Turns on the VPC's internal DNS, so instances resolve names such as <code class=\"inline\">ip-10-0-1-42.us-east-2.compute.internal</code>."),
            ("two aws_subnet blocks", "<code class=\"inline\">public</code> in <code class=\"inline\">10.0.1.0/24</code> and <code class=\"inline\">private</code> in <code class=\"inline\">10.0.2.0/24</code>. Subnet ranges may not overlap, and each is pinned to exactly one zone."),
            ("availability_zone = var.public_subnet_az", "Comes from a plain variable, defaulting to <code class=\"inline\">us-east-2a</code> and <code class=\"inline\">us-east-2b</code>. This lab is explicit about its zones rather than resolving them from a data source; Lab 10 shows the data-source form."),
            ("\"public\" is a name, not a setting", "Nothing makes that subnet public: there is no internet gateway and no route to one, so both subnets are private today. The name records the role it will play in Lab 10."),
            ("vpc_id on the security group", "Places the group in the VPC this configuration created. A group without <code class=\"inline\">vpc_id</code> would fall back to the account's default VPC, which is exactly what this lab avoids."),
            ("cidr_blocks = [var.vpc_cidr]", "Port 22 is reachable only from <code class=\"inline\">10.0.0.0/16</code>, this VPC's own range. Never <code class=\"inline\">0.0.0.0/0</code> on an administrative port."),
            ("egress protocol = \"-1\"", "<code class=\"inline\">-1</code> means every protocol, so the instance can reach package mirrors once a route out exists. Groups are stateful, so replies to allowed inbound traffic need no rule."),
            ("subnet_id on the instance", "Places the instance in the public subnet deliberately. Combined with <code class=\"inline\">vpc_security_group_ids</code>, nothing about this instance's network is inherited."),
            ("instance_type = var.instance_type", "Defaults to <code class=\"inline\">t3.micro</code>, the smallest general-purpose size used throughout this track."),
            ("tags = { Lab = \"lab03\" }", "Every AWS resource in this track carries <code class=\"inline\">Name</code> and <code class=\"inline\">Lab</code> tags so leftovers are easy to find and delete."),
        ],
        lang_note=(
            "<strong>This instance is deliberately unreachable.</strong> There is no internet "
            "gateway, no route to one, and no public IP, so you cannot SSH to it from your "
            "laptop and it cannot reach the internet. That is the point: the lab teaches "
            "resources, data sources and network placement without also owing you a working "
            "public service. Making something publicly reachable is the "
            "<a class=\"lablink\" href=\"#lab10-capstone-vpc-ec2\">Lab 10 capstone</a>'s payoff, "
            "and it needs three more resources to get there."
        ),
        lab=3,
    ),
    dict(
        eyebrow="Lab 04 &middot; Workflow",
        heading="The core loop: init, plan, apply, destroy",
        concept=(
            "<code class=\"inline\">plan</code> compares your configuration against state and "
            "prints what it would change, without changing anything. "
            "<code class=\"inline\">apply</code> carries out that plan. "
            "<code class=\"inline\">destroy</code> removes everything the configuration owns. "
            "This lab runs the loop against a real VPC, which AWS provides free of charge, so the "
            "lifecycle is genuine rather than simulated."
        ),
        code=esc('''resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
  numeric = false
}

resource "aws_vpc" "lifecycle" {
  cidr_block         = "10.4.0.0/16"
  enable_dns_support = true

  tags = {
    Lab  = "lab04"
    Name = "lab04-${random_string.suffix.result}"
  }
}

# Plan: 2 to add, 0 to change, 0 to destroy.'''),
        rows=[
            ("two resources, one dependency", "The VPC's Name tag reads <code class=\"inline\">random_string.suffix.result</code>, so Terraform must create the string first. The apply log shows that ordering."),
            ("Plan: 2 to add, 0 to change, 0 to destroy.", "The summary line. Read it before every apply &mdash; the counts are the fastest check that you are changing what you think you are."),
            ("a VPC is free", "An empty VPC costs nothing. It is the smallest real thing AWS will build, which makes it the right subject for a lab about the lifecycle itself."),
            ("its own VPC", "The lab never touches the account's default VPC, so it cannot fail with <code class=\"inline\">VPCIdNotSpecified</code> on an account that has none."),
            ("plan again after apply", "It reports no changes. That is Terraform comparing state against reality, not remembering what it just did."),
            ("destroy", "Removes both resources in reverse dependency order: the VPC first, then the string it depended on."),
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
    dict(
        eyebrow="Lab 06 &middot; Inputs",
        heading="Variables, locals, and outputs",
        concept=(
            "An <em>input variable</em> is a knob on your configuration: declare it with a "
            "<code class=\"inline\">type</code> and a <code class=\"inline\">description</code>, "
            "then the same code can build training and production by passing different values. A "
            "<em>local</em> is a computed value used inside the module only &mdash; ideal for "
            "merged tag maps. An <em>output</em> exports a value after apply for operators or for "
            "another configuration to read. The network the instance needs is itself parameterised "
            "here: the VPC, subnet and security group are all driven by typed variables."
        ),
        code=esc('''variable "server_name" {
  type        = string
  description = "Value used for the Name tag on the EC2 instance."
  default     = "lab06-web"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance size. Must be a t3 size to keep this lab cheap."
  default     = "t3.micro"
  nullable    = false

  validation {
    condition     = startswith(var.instance_type, "t3.")
    error_message = "instance_type must be a t3 size, for example t3.micro."
  }
}

variable "vpc_cidr" {
  type        = string
  description = "Address range of the VPC this lab creates. Also the only source allowed to reach port 22."
  default     = "10.0.0.0/16"
}

variable "subnet_cidr" {
  type        = string
  description = "Address range of the subnet the instance launches into. Must sit inside vpc_cidr."
  default     = "10.0.1.0/24"
}

variable "subnet_az" {
  type        = string
  description = "Availability zone the subnet is created in. Must belong to aws_region."
  default     = "us-east-2a"
}

variable "tags" {
  type        = map(string)
  description = "A map: values addressed by string key. Merged into every resource tag set."
  default = {
    Environment = "training"
    Owner       = "platform-team"
  }
}

locals {
  common_tags = merge(var.tags, {
    Name = var.server_name
    Lab  = "lab06"
  })
}

resource "aws_vpc" "main" {
  cidr_block         = var.vpc_cidr
  enable_dns_support = true
  tags               = local.common_tags
}

resource "aws_subnet" "main" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.subnet_cidr
  availability_zone = var.subnet_az
  tags              = local.common_tags
}

resource "aws_security_group" "instance" {
  name        = "${var.server_name}-sg"
  description = "Lab 06 instance security group"
  vpc_id      = aws_vpc.main.id
  tags        = local.common_tags

  ingress {
    description = "SSH from inside the VPC only"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.main.id
  vpc_security_group_ids = [aws_security_group.instance.id]
  tags                   = local.common_tags
}

output "instance_id" {
  description = "EC2 instance ID, for the console and for later labs."
  value       = aws_instance.web.id
}'''),
        rows=[
            ("variable \"server_name\"", "Declares an input. Its address elsewhere in the configuration is <code class=\"inline\">var.server_name</code>."),
            ("type = string", "Terraform rejects a non-string value at plan time instead of failing mid-apply. Every variable in this track declares a type."),
            ("description", "Required by the track's own rules: it is the documentation a module consumer reads."),
            ("default", "Makes the variable optional. Omit the default when a value must always be supplied deliberately."),
            ("nullable = false", "Rejects an explicit <code class=\"inline\">null</code>, so the default cannot be overridden into nothing."),
            ("validation { condition }", "A rule checked at plan time. <code class=\"inline\">startswith</code> keeps the lab on a cheap instance family, and the <code class=\"inline\">error_message</code> is what the learner sees."),
            ("type = map(string)", "A map of string keys to string values, written <code class=\"inline\">{ Key = \"value\" }</code> in HCL."),
            ("locals { ... }", "Values computed once and reused. Not settable from outside the module."),
            ("merge(var.tags, { ... })", "Combines maps into one. On a key collision the later map wins, so <code class=\"inline\">Name</code> here overrides any inherited <code class=\"inline\">Name</code>."),
            ("aws_vpc.main / aws_subnet.main", "The lab builds its own one-subnet network from <code class=\"inline\">var.vpc_cidr</code> and <code class=\"inline\">var.subnet_cidr</code>, so changing a variable changes the network rather than the code."),
            ("availability_zone = var.subnet_az", "A plain variable, defaulting to <code class=\"inline\">us-east-2a</code>. A subnet is zonal, so it must name exactly one zone."),
            ("vpc_id on the security group", "Places the group in the VPC this configuration created, so nothing here depends on the account's default VPC."),
            ("cidr_blocks = [var.vpc_cidr]", "One variable serves two purposes: it sizes the VPC and it is the only range allowed to reach port 22. Never <code class=\"inline\">0.0.0.0/0</code> on SSH."),
            ("subnet_id / vpc_security_group_ids", "Wires the instance to the subnet and group above. Both are references, so Terraform builds the VPC, then the subnet and group, then the instance."),
            ("tags = local.common_tags", "One reference gives every resource the same tag set. Change <code class=\"inline\">var.tags</code> once and all of them update."),
            ("output \"instance_id\"", "Printed after apply and readable with <code class=\"inline\">terraform output instance_id</code>."),
        ],
        lang_note=(
            "<strong>This instance is deliberately unreachable.</strong> The lab creates no "
            "internet gateway, no route to one, and no public IP, and port 22 is open only to "
            "the VPC's own range &mdash; so there is nothing to connect to from outside. Public "
            "reachability is the <a class=\"lablink\" href=\"#lab10-capstone-vpc-ec2\">Lab 10 "
            "capstone</a>'s payoff. What this lab teaches is the type system: string, number, "
            "bool, list, set, map, object, tuple, <code class=\"inline\">optional()</code>, "
            "<code class=\"inline\">any</code>, <code class=\"inline\">null</code>, and "
            "<code class=\"inline\">sensitive</code>."
        ),
        lab=6,
    ),
    dict(
        eyebrow="Lab 07 &middot; Values and secrets",
        heading="tfvars files, value precedence, and sensitive",
        concept=(
            "A <code class=\"inline\">terraform.tfvars</code> file supplies values for variables "
            "that have no default, and Terraform loads it automatically. Secrets are the "
            "exception: mark them <code class=\"inline\">sensitive</code> and pass them by "
            "environment variable, because a tfvars file is a file like any other and gets "
            "committed by accident. This lab tags a real VPC from those values so you can read "
            "them back off AWS &mdash; and see that the password is not among them."
        ),
        code=esc('''variable "project"     { type = string }     # no default, so required
variable "environment" { type = string }     # validated: dev | test | prod
variable "cost_code"   { type = string }     # validated: exactly 3 characters

variable "db_password" {
  type      = string
  sensitive = true                           # never written to tfvars
}

locals {
  common_tags = {
    Lab         = "lab07"
    Name        = "${var.project}-${var.environment}"
    Project     = var.project
    Environment = var.environment
    CostCode    = var.cost_code
  }
}

resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr
  tags       = local.common_tags
}'''),
        rows=[
            ("no default", "A variable without a default is mandatory. Terraform refuses to plan until it is supplied, which is why this lab needs a <code class=\"inline\">terraform.tfvars</code> file and most others do not."),
            ("validation blocks", "<code class=\"inline\">environment</code> must be dev, test or prod; <code class=\"inline\">cost_code</code> must be exactly three characters. Bad input fails at plan with your message, not at apply with an AWS one."),
            ("sensitive = true", "Redacts the value in plan and apply output. It does <em>not</em> encrypt it &mdash; the value is still plain text inside the state file."),
            ("db_password is absent from common_tags", "Deliberate. A tag is readable by anyone holding describe permission on the account, so a secret in a tag is a published secret."),
            ("TF_VAR_db_password", "Terraform reads any environment variable named <code class=\"inline\">TF_VAR_&lt;name&gt;</code> as that variable, which keeps the password off disk entirely."),
            ("reading the tags back", "<code class=\"inline\">aws ec2 describe-vpcs</code> shows Project, Environment and CostCode on the real VPC. That is the proof the tfvars values reached AWS."),
            ("precedence", "<code class=\"inline\">-var</code> beats <code class=\"inline\">terraform.tfvars</code>, which beats the variable's default. Overriding one now changes a tag on a real resource rather than only an output."),
        ],
        lab=7,
    ),
    dict(
        eyebrow="Lab 08 &middot; State",
        heading="Local state, refresh, and drift",
        concept=(
            "With no backend configured, Terraform writes "
            "<code class=\"inline\">terraform.tfstate</code> beside your configuration. It maps "
            "each resource address to the real object's ID and to every attribute AWS returned. "
            "This lab puts a real VPC in state, so the file holds an ID that AWS also holds "
            "&mdash; which is what makes losing the file an incident rather than an inconvenience."
        ),
        code=esc('''resource "random_pet" "server" {
  prefix = "lab08"
  length = 2
}

resource "random_password" "db" {
  length  = 16
  special = false
}

resource "aws_vpc" "main" {
  cidr_block = "10.8.0.0/16"

  tags = {
    Lab  = "lab08"
    Name = random_pet.server.id
  }
}

# terraform state list
# aws_vpc.main
# random_password.db
# random_pet.server'''),
        rows=[
            ("no backend block", "State goes to <code class=\"inline\">./terraform.tfstate</code>. Fine for one person learning, unworkable for a team &mdash; which is what labs 17 to 19 solve."),
            ("terraform state list", "Prints the three addresses Terraform tracks. Addresses, not names: this is how you refer to a resource in every state command."),
            ("terraform state show aws_vpc.main", "Shows roughly twenty attributes against the two you wrote. Everything else was assigned by AWS and recorded at apply."),
            ("random_password in state", "Stored as plain text. State is a secret-bearing file: never commit it, and prefer a backend that encrypts at rest."),
            ("losing the file", "The VPC still exists but Terraform no longer knows about it. The next apply builds a <em>second</em> one, and the first becomes an orphan nobody manages."),
            ("drift", "Change a tag in the console, then run <code class=\"inline\">plan</code>. Terraform refreshes, sees reality differ from state, and proposes putting it back."),
        ],
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
        eyebrow="Lab 10 &middot; Capstone",
        heading="The whole picture: VPC, IGW, route table, subnet, SG, EC2",
        concept=(
            "The capstone builds a working public web server from nothing. An "
            "<em>internet gateway</em> attaches the VPC to the internet; a <em>route table</em> "
            "with a default route to that gateway is what makes a subnet <em>public</em>; the "
            "security group opens port 80; and <code class=\"inline\">user_data</code> "
            "installs a web server on first boot. The output is a URL you can actually open. It "
            "sits mid-track on purpose: everything up to here is a piece, and this is the first "
            "lab where the pieces make something a person can use &mdash; Labs 03 and 06 build "
            "networks, but neither is reachable from outside."
        ),
        code=esc('''data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr   # 10.0.0.0/16
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = merge(local.common_tags, { Name = local.name })
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = merge(local.common_tags, { Name = "${local.name}-igw" })
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidr   # 10.0.1.0/24
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

resource "aws_security_group" "web" {
  name        = "${local.name}-web"
  description = "Allow inbound web traffic, all outbound"
  vpc_id      = aws_vpc.this.id

  # One literal rule. Only HTTP is needed: the instance has no key pair.
  ingress {
    description = "Inbound HTTP"
    from_port   = var.http_port      # 80
    to_port     = var.http_port
    protocol    = "tcp"
    cidr_blocks = [var.allowed_cidr] # 0.0.0.0/0
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, { Name = "${local.name}-web-sg" })
}

resource "aws_instance" "web" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type   # t3.micro
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]

  user_data = <<-EOT
    #!/bin/bash
    dnf install -y httpd
    systemctl enable --now httpd
    echo "<h1>${local.name} is live</h1>" > /var/www/html/index.html
  EOT

  tags = merge(local.common_tags, { Name = "${local.name}-web" })

  depends_on = [aws_route_table_association.public]
}

output "web_url" {
  value = "http://${aws_instance.web.public_ip}"
}'''),
        rows=[
            ("aws_vpc, cidr_block", "The private network, with room for 65,536 addresses. Every other resource here lives inside it."),
            ("enable_dns_hostnames", "Gives instances public DNS names as well as IPs. Required before public hostnames resolve."),
            ("aws_internet_gateway", "Attaches the VPC to the internet. On its own it routes nothing. This is the resource Labs 03 and 06 deliberately leave out."),
            ("data.aws_availability_zones", "Asks the account which zones it can actually use. Zone names are mapped per account, so a hardcoded <code class=\"inline\">us-east-2a</code> is not the same hardware everywhere and may not exist or have capacity in yours."),
            ("names[0]", "Takes the first usable zone. The subnet is zonal, so it must name exactly one."),
            ("map_public_ip_on_launch", "Instances launched in this subnet get a public IP automatically."),
            ("route { 0.0.0.0/0 }", "The default route: any destination not inside the VPC goes to the gateway. This line is what makes the subnet public."),
            ("aws_route_table_association", "Binds the route table to the subnet. Skip it and the subnet silently keeps the VPC's main table and stays private."),
            ("one literal ingress block", "The group needs exactly one rule, so it is written out rather than generated. <code class=\"inline\">var.http_port</code> is a single number defaulting to <code class=\"inline\">80</code>. There is deliberately no SSH rule: the instance has no key pair and nothing here connects to it. <a class=\"lablink\" href=\"#lab21-dynamic-blocks\">Lab 21</a> is the case where a <code class=\"inline\">dynamic</code> block earns its keep."),
            ("cidr_blocks = [var.allowed_cidr]", "Defaults to <code class=\"inline\">0.0.0.0/0</code> so the lab works from any network. Narrow it to <code class=\"inline\">YOUR_IP/32</code> in any account you care about."),
            ("subnet_id on the instance", "Places the instance in the public subnet. Combined with the route and the public IP, the server becomes reachable."),
            ("user_data = &lt;&lt;-EOT", "A heredoc script the cloud runs once on first boot. <code class=\"inline\">&lt;&lt;-</code> strips the leading indentation."),
            ("dnf install -y httpd", "Amazon Linux 2023 uses <code class=\"inline\">dnf</code>. Running it here needs no SSH and no provisioner."),
            ("depends_on = [aws_route_table_association.public]", "The instance reads no attribute from the association, so Terraform sees no dependency &mdash; but <code class=\"inline\">dnf install</code> needs working internet routing. This is the textbook case for an explicit <code class=\"inline\">depends_on</code>: a real dependency no reference expresses."),
            ("output web_url", "Builds the browsable URL from the assigned public IP. This is the observable proof the stack works."),
        ],
        lang_note="This lab bills for real. Run <code class=\"inline\">terraform destroy</code> as soon "
                  "as you have loaded the page. Lab 22 builds the same topology again with its "
                  "state in S3, once you have met remote backends.",
        lab=10,
    ),
    dict(
        eyebrow="Lab 11 &middot; Collections",
        heading="Lists, sets and maps, and the for expression",
        concept=(
            "HCL has three collection types. A <strong>list</strong> is ordered and keeps "
            "duplicates, addressed by position. A <strong>set</strong> is unordered and discards "
            "duplicates. A <strong>map</strong> is keyed by string. A <em>for expression</em> "
            "builds a new collection from an existing one, and the shape of the result follows "
            "the brackets: <code class=\"inline\">[ ]</code> gives a list, "
            "<code class=\"inline\">{ }</code> gives a map. The map then does real work &mdash; "
            "it supplies the CIDR and zone of an actual subnet, so changing a map entry changes "
            "AWS. The lab builds a free VPC and subnet, so it needs credentials."
        ),
        code=esc('''variable "subnets" {
  type = map(object({ cidr = string, az = string }))
  default = {
    app_a = { cidr = "10.0.1.0/24", az = "us-east-2a" }
    app_b = { cidr = "10.0.2.0/24", az = "us-east-2b" }
  }
}

locals {
  unique_tag_names = sort(tolist(toset(var.tag_names)))
  tag_labels       = [for name in var.tag_names : upper(name)]
  subnet_cidrs     = { for name, subnet in var.subnets : name => subnet.cidr }
  zone_a_subnets   = [for name, subnet in var.subnets : name if subnet.az == "us-east-2a"]
}

# Map indexing doing real work: one object selected by key, two of its
# attributes reached with a dot. Change the map entry and AWS changes.
#
# One resource block is still one subnet. Creating one per map entry needs
# the for_each meta-argument, which Lab 24 introduces.
resource "aws_subnet" "app_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = var.subnets["app_a"].cidr
  availability_zone = var.subnets["app_a"].az
}'''),
        rows=[
            ("map(object({ cidr, az }))", "A map whose values are structured. Terraform checks at plan time that every entry has both attributes with the right types."),
            ("toset(var.tag_names)", "Converts the list to a set, silently dropping the repeated entry. Converting back with <code class=\"inline\">tolist()</code> is what lets <code class=\"inline\">sort()</code> apply."),
            ("sort(...)", "A set has no order of its own, so Terraform may render it in any sequence. Sorting makes the output stable between runs."),
            ("[for name in var.tag_names : upper(name)]", "A for expression over a list. Square brackets mean a list result, one element per input, order preserved."),
            ("{ for name, subnet in var.subnets : name =&gt; subnet.cidr }", "Iterating a map yields two loop variables, key and value. Braces and <code class=\"inline\">=&gt;</code> mean a map result."),
            ("if subnet.az == \"us-east-2a\"", "An optional if clause filters entries out of the result. Only subnets in that zone survive."),
            ("var.subnets[\"app_a\"].cidr", "Square brackets select one object by key; the dot reaches one of its attributes. This is the value AWS actually receives as the subnet's CIDR."),
            ("why not count or for_each here", "Those meta-arguments turn a collection into many <em>resources</em>, which is a different subject. Lab 24 covers it. This lab is about the collections themselves."),
            ("addressing by key beats by position", "Because the subnet names a key rather than an index, removing <code class=\"inline\">app_b</code> from the map leaves the real subnet untouched. A positional reference would have shifted and replaced it."),
        ],
        lab=11,
    ),
    dict(
        eyebrow="Lab 12 &middot; Functions",
        heading="Built-in functions transform values at plan time",
        concept=(
            "HCL has no loops and no user-defined functions, but it ships a large library of "
            "built-in ones for strings, collections, CIDR arithmetic and encoding. They evaluate "
            "during plan, so results are visible before anything is created, and "
            "<code class=\"inline\">terraform console</code> lets you try an expression before "
            "committing it to a file. Here the results are consumed by real resources rather than "
            "only printed: a computed CIDR becomes a subnet, and a deduplicated list becomes a "
            "security group's ingress ranges."
        ),
        code=esc('''locals {
  slug          = lower(replace(var.application, " ", "-"))
  unique_cidrs  = sort(tolist(toset(var.cidrs)))
  cidr_count    = length(local.unique_cidrs)
  subnet_prefix = cidrsubnet(var.vpc_cidr, var.subnet_newbits, var.subnet_netnum)
  summary       = format("%s uses %d unique CIDR(s)", local.slug, local.cidr_count)
}

resource "aws_subnet" "derived" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = local.subnet_prefix   # never typed by hand
  availability_zone = var.subnet_az
}

resource "aws_security_group" "app" {
  vpc_id = aws_vpc.main.id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = local.unique_cidrs        # deduplicated and sorted
  }
}'''),
        rows=[
            ("lower(replace(...))", "Functions nest: the inner call runs first. This turns <code class=\"inline\">\"Payments API\"</code> into <code class=\"inline\">payments-api</code>, safe for a resource name."),
            ("sort(tolist(toset(var.cidrs)))", "Three functions in sequence: drop duplicates, convert back to a list, then order it. The result becomes the security group's real source ranges."),
            ("cidrsubnet(var.vpc_cidr, newbits, netnum)", "Carves a subnet out of a larger range. Derived from the VPC's own CIDR, so widening the VPC moves the subnet with it and neither is retyped."),
            ("becomes aws_subnet.derived.cidr_block", "This is the difference from printing it. Change <code class=\"inline\">var.vpc_cidr</code> and the plan replaces both the VPC and the subnet together."),
            ("format(\"%s uses %d ...\")", "Builds a display string with typed placeholders. <code class=\"inline\">%d</code> requires a number, so a type error is caught at plan."),
            ("jsonencode stays an output", "Its real destination is an IAM policy document, which this track does not cover. Printed here so you can see the encoding, not wired to a resource."),
            ("terraform console", "An interactive prompt against your real variables and locals. Try an expression there before you put it in a file."),
        ],
        lab=12,
    ),
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
  required_version = ">= 1.5.0"
  required_providers {
    aws    = { source = "hashicorp/aws", version = "~> 5.0" }
    random = { source = "hashicorp/random", version = "~> 3.0" }
  }
}

provider "aws" { region = var.aws_region }   # var.aws_region defaults to us-east-2
provider "random" {}

resource "random_pet" "label" { length = 2 }

output "provider_composition" {
  value = { aws_region = var.aws_region, generated_label = random_pet.label.id }
}

# ---------------------------------------------------------------------------
# Everything below is the ALIAS PATTERN, not part of lab13. The lab stops above.
# Two configurations of the SAME provider need an alias. Copy this into your own
# work when you need a second region; add the variable, or the snippet will not
# plan.
# ---------------------------------------------------------------------------
variable "secondary_region" {
  type        = string
  description = "A region other than var.aws_region, for the aliased provider."
  default     = "us-east-1"
}

provider "aws" {
  alias  = "secondary"
  region = var.secondary_region
}

resource "aws_vpc" "secondary" {
  provider   = aws.secondary
  cidr_block = "10.90.0.0/16"

  tags = { Name = "${random_pet.label.id}-secondary", Lab = "lab13" }
}'''),
        rows=[
            ("two required_providers entries", "Each provider is a separate plugin download and a separate credential context. <code class=\"inline\">init</code> fetches both."),
            ("provider \"aws\" { region = ... }", "Runtime configuration for the AWS plugin. No alias, so this is the default: any AWS resource that says nothing about providers uses it."),
            ("provider \"random\" {}", "A provider with nothing to configure still gets a block. It needs no credentials and reaches no API, so it is free to apply."),
            ("resource \"random_pet\" \"label\"", "The one resource this lab creates. Two providers are declared and only one of them builds anything &mdash; declaring a provider does not oblige you to use it."),
            ("output provider_composition", "Prints one value from each side, which is the observable proof that both plugins loaded and ran."),
            ("alias = \"secondary\"", "Names a second AWS configuration. Its address is <code class=\"inline\">aws.secondary</code>, and the unaliased block stays the default."),
            ("variable \"secondary_region\"", "Declared here so the pattern below stands on its own. Without it the snippet references an undeclared variable and fails at <code class=\"inline\">plan</code>. It is not in the lab's own <code class=\"inline\">variables.tf</code>."),
            ("region = var.secondary_region", "The alias exists to hold a <em>different</em> region from the default. The labs run in us-east-2, so the second one is us-east-1."),
            ("provider = aws.secondary", "Sends this one resource to the aliased configuration. Omit the argument and it silently lands in the default region instead &mdash; a mistake no plan will flag."),
            ("random_pet.label.id in a tag", "A cross-provider reference. Terraform orders the graph so the generated name exists before the VPC is created. This resource is part of the pattern, not of lab13 &mdash; the lab creates only the <code class=\"inline\">random_pet</code>."),
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
  default     = "local-exec completed"
  description = "Text the local-exec provisioner prints on the machine running Terraform."
}

resource "terraform_data" "local_action" {
  input = var.message
  provisioner "local-exec" {
    command = "printf '%s\\n' '${self.input}'"
  }
  # Runs before the resource is destroyed instead of after creation.
  # A destroy-time provisioner may reference self, but not var or other resources.
  provisioner "local-exec" {
    when    = destroy
    command = "printf 'destroying %s\\n' '${self.input}'"
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
            ("when = destroy", "Runs before the resource is destroyed instead of after creation. If it fails, the destroy is <strong>blocked</strong> and the resource stays in state."),
            ("self in a destroy provisioner", "A destroy-time provisioner may only reference <code class=\"inline\">self</code>, <code class=\"inline\">count.index</code> or <code class=\"inline\">each.key</code>. Using <code class=\"inline\">var.message</code> here fails at validate."),
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
            ("prefer user_data", "The same two commands in <code class=\"inline\">user_data</code> need no inbound SSH, no key on the Terraform host, and no reachability. Labs 10 and 22 do it that way."),
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
            "<code class=\"inline\">default</code> coexist from identical code. This lab builds "
            "one free VPC per workspace, so two exist in the account at once and "
            "<code class=\"inline\">state list</code> in either shows only its own &mdash; the "
            "isolation claim, tested rather than asserted."
        ),
        code=esc('''variable "workspace_cidrs" {
  type = map(string)
  default = {
    default = "10.16.0.0/16"
    dev     = "10.17.0.0/16"
  }
}

locals {
  name     = "lab16-${terraform.workspace}"
  vpc_cidr = lookup(var.workspace_cidrs, terraform.workspace, "10.18.0.0/16")
}

resource "aws_vpc" "env" {
  cidr_block = local.vpc_cidr

  tags = {
    Lab         = "lab16"
    Name        = local.name
    Environment = terraform.workspace
  }
}

# terraform workspace new dev
# terraform workspace select dev
# terraform apply'''),
        rows=[
            ("terraform.workspace", "A built-in value holding the active workspace name. No variable declares it, and it is available anywhere in the configuration."),
            ("lookup(map, key, fallback)", "Selects this workspace's CIDR, falling back to a third range for any workspace name not in the map. Without distinct CIDRs the two VPCs would overlap."),
            ("Name = \"lab16-${terraform.workspace}\"", "Interpolating the workspace into every name is what stops two workspaces colliding on an AWS name. Omit it and the second apply fails."),
            ("two VPCs at once", "After applying in both workspaces, <code class=\"inline\">describe-vpcs</code> shows both. Each state file lists only its own &mdash; that is the isolation."),
            ("what a workspace is not", "Both VPCs live in one account under one set of credentials. A workspace separates <em>state</em>, not blast radius. Production deserves a separate account, or at least separate state keys as in Lab 18."),
            ("workspace select dev", "Switches without creating. Always run <code class=\"inline\">workspace show</code> before an apply you care about."),
            ("do not destroy yet", "Lab 20 reads both of this lab's state files, so its cleanup is deliberately deferred until after that lab."),
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
# region       = "us-east-2"
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
            ("terraform output -raw vpc_id", "Third check, and the most concrete. Record the VPC ID before migrating and compare it after: an identical ID proves the state moved while the infrastructure did not."),
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
    region = "us-east-2"
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
            ("in this lab", "The producer is Lab 16, read over the <code class=\"inline\">local</code> backend rather than S3, and it publishes a real <code class=\"inline\">vpc_id</code> and <code class=\"inline\">vpc_cidr</code>. The consumer reads a genuine VPC ID out of a state file while making no AWS call of its own."),
        ],
        lab=20,
    ),
    dict(
        eyebrow="Lab 21 &middot; Dynamic blocks",
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
  name_prefix = "lab21-dynamic-"
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

  tags = { Name = "lab21-dynamic-sg", Lab = "lab21" }
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
            "<code class=\"inline\">aws ec2 create-default-vpc</code>. Only this lab and Lab 15 "
            "still need one; every other AWS lab in the track builds its own network and sets "
            "<code class=\"inline\">subnet_id</code> and <code class=\"inline\">vpc_id</code> "
            "explicitly, which is the better pattern."
        ),
        lab=21,
    ),
    dict(
        eyebrow="Lab 22 &middot; Remote state in practice",
        heading="The capstone rebuilt with its state in S3",
        concept=(
            "Lab 10 built a public web server with state on your laptop. Lab 22 builds the same "
            "topology with the state object in S3 and native locking switched on, which is how "
            "the stack would actually be run by a team. Nothing about the resources changes; "
            "what changes is where the record of them lives, so the backend is supplied at "
            "<code class=\"inline\">init</code> time through "
            "<code class=\"inline\">-backend-config</code> rather than written into the code."
        ),
        code=esc('''terraform {
  # Same floor as labs 17-19: use_lockfile is generally available from 1.11.
  required_version = ">= 1.11.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {}
}

locals {
  name = "${var.project}-remote"

  common_tags = {
    Lab     = "lab22"
    Project = var.project
  }
}

# backend.hcl.example -> copy to backend.hcl and fill in
# bucket       = "replace-with-your-globally-unique-state-bucket"
# key          = "labs/lab22/terraform.tfstate"
# region       = "us-east-2"
# encrypt      = true
# use_lockfile = true

# terraform init -backend-config=backend.hcl'''),
        rows=[
            ("backend \"s3\" {}", "Partial configuration. The bucket, key and region arrive at <code class=\"inline\">init</code>, because a backend block cannot reference a variable."),
            ("required_version &gt;= 1.11.0", "Same reason as labs 17 to 19: <code class=\"inline\">use_lockfile</code> is experimental in 1.10 and generally available from 1.11."),
            ("key = labs/lab22/...", "A distinct key, so this lab's state cannot overwrite lab 17's or lab 19's in the same bucket."),
            ("use_lockfile = true", "Native S3 locking. Terraform writes <code class=\"inline\">&lt;key&gt;.tflock</code> beside the state object while the apply runs."),
            ("same resources as Lab 10", "VPC, internet gateway, public subnet, route table and association, security group, and the user-data web server. Only the state location differs."),
            ("Lab = \"lab22\"", "The tag that distinguishes this build from the Lab 10 capstone if both are applied in one account."),
            ("depends_on on the instance", "Forces the route table association to exist before the instance launches, so the first boot already has a path out for <code class=\"inline\">dnf</code>."),
        ],
        lang_note="This lab bills for real, and it also leaves an object in your state bucket. "
                  "Run <code class=\"inline\">terraform destroy</code> when you have loaded the "
                  "page; the state object and its bucket are yours to remove separately.",
        lab=22,
    ),
    dict(
        eyebrow="Lab 23 &middot; Storage",
        heading="An S3 bucket as a managed resource",
        concept=(
            "Every earlier S3 bucket in this track was somebody else's: a state store you created "
            "by hand so Terraform could write to it. Lab 23 turns the bucket itself into a managed "
            "resource. Bucket names are globally unique across all AWS accounts, and the modern "
            "provider splits what used to be one giant resource into a small core resource plus "
            "one resource per feature &mdash; versioning, encryption, public access &mdash; which "
            "is why a safe bucket is four blocks rather than four arguments."
        ),
        code=esc('''locals {
  bucket_name = "${var.bucket_prefix}-${random_pet.suffix.id}"
}

resource "random_pet" "suffix" {
  length    = 2
  separator = "-"
}

resource "aws_s3_bucket" "lab" {
  bucket        = local.bucket_name
  force_destroy = var.force_destroy

  tags = merge(local.common_tags, { Name = local.bucket_name })
}

resource "aws_s3_bucket_versioning" "lab" {
  bucket = aws_s3_bucket.lab.id

  versioning_configuration {
    status = var.versioning_status
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "lab" {
  bucket = aws_s3_bucket.lab.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "lab" {
  bucket = aws_s3_bucket.lab.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}'''),
        rows=[
            ("aws_s3_bucket", "The core resource. In provider 5.x it carries almost no settings of its own; each feature moved into a resource of its own, keyed by bucket name. Older tutorials showing these as inline blocks describe provider 3.x."),
            ("random_pet.suffix", "Bucket names are globally unique across every AWS account, so a fixed name collides the moment a second learner applies. Two random words make the name safe without editing the file."),
            ("force_destroy", "Lets <code class=\"inline\">destroy</code> delete a bucket that still holds objects. Correct for a throwaway lab, dangerous anywhere else."),
            ("aws_s3_bucket_versioning", "Keeps previous object versions. This is the setting that makes a state bucket recoverable after a bad apply, which is why labs 17 to 19 and 22 asked for it."),
            ("aws_s3_bucket_server_side_encryption_configuration", "Encrypts objects at rest with S3-managed keys. State files hold sensitive values in plain text, so this is not optional in practice."),
            ("aws_s3_bucket_public_access_block", "Four independent switches that together make accidental public exposure impossible. Set all four unless you are deliberately hosting a public site."),
            ("bucket = aws_s3_bucket.lab.id", "Every feature resource references the core one, which is what orders the graph and ties them together in state."),
        ],
        lang_note="Terraform cannot manage the bucket its own state lives in: creating it would need "
                  "a working backend, and the backend needs the bucket. That is why labs 17 to 19 "
                  "and 22 create the state bucket out of band. This lab keeps its own state local, "
                  "so the bucket is an ordinary managed resource with nothing circular about it.",
        lab=23,
    ),
    dict(
        eyebrow="Lab 24 &middot; Meta-arguments",
        heading="count by position, for_each by name",
        concept=(
            "Both meta-arguments build many resources from one block, and the difference only "
            "shows up when the input changes. A <code class=\"inline\">count</code> instance is "
            "addressed by its <strong>position</strong> &mdash; "
            "<code class=\"inline\">aws_s3_bucket.by_count[1]</code> &mdash; so deleting an item "
            "from the middle of the list shifts every later item down a slot, and Terraform reads "
            "that shift as a change to each one. A <code class=\"inline\">for_each</code> instance "
            "is addressed by its <strong>key</strong> &mdash; "
            "<code class=\"inline\">aws_s3_bucket.by_each[\"assets\"]</code> &mdash; so removing a "
            "key touches only that resource and leaves its neighbours alone."
        ),
        code=esc('''# count: N interchangeable copies, addressed by POSITION.
resource "aws_s3_bucket" "by_count" {
  count = length(var.bucket_names)

  bucket        = "${local.prefix}-count-${var.bucket_names[count.index]}"
  force_destroy = true

  tags = merge(local.common_tags, {
    Name  = "${local.prefix}-count-${var.bucket_names[count.index]}"
    Index = tostring(count.index)
  })
}

# for_each: N differently-configured instances, addressed by NAME.
resource "aws_s3_bucket" "by_each" {
  for_each = var.buckets

  bucket        = "${local.prefix}-${each.key}"
  force_destroy = true

  tags = merge(each.value.tags, local.common_tags, {
    Name = "${local.prefix}-${each.key}"
  })
}

resource "aws_s3_bucket_versioning" "by_each" {
  for_each = var.buckets

  bucket = aws_s3_bucket.by_each[each.key].id

  versioning_configuration {
    status = each.value.versioning ? "Enabled" : "Suspended"
  }
}'''),
        rows=[
            ("count = length(var.bucket_names)", "Instance count comes from a list. Addresses are <code class=\"inline\">[0]</code>, <code class=\"inline\">[1]</code>, <code class=\"inline\">[2]</code> &mdash; position is the only identity each one has."),
            ("count.index", "The current position. Because the name is derived from it, changing the list order rewrites names."),
            ("for_each = var.buckets", "Iterates a map. Requires a map or a set, never a list &mdash; a list would reintroduce positional addressing."),
            ("each.key / each.value", "The key names the instance and appears in its address; the object under it configures that one instance, so no two need to match."),
            ("aws_s3_bucket.by_each[each.key].id", "A keyed reference into another for_each resource. Both blocks iterate the same map, so the keys line up."),
            ("each.value.versioning ? ...", "Per-instance configuration &mdash; the real reason to choose for_each. A count block cannot vary settings between copies."),
        ],
        lang_note="Removing the middle item shows the cost of position. Deleting "
                  "<code class=\"inline\">assets</code> from the list gives "
                  "<code class=\"inline\">1 to add, 0 to change, 2 to destroy</code>: index [1] is "
                  "<em>replaced</em>, because a bucket name is immutable and index [1] must now "
                  "become <code class=\"inline\">backups</code>. Deleting the same key from the map "
                  "gives <code class=\"inline\">0 to add, 0 to change, 2 to destroy</code>, and both "
                  "destroyed resources belong to the removed key &mdash; the surviving buckets do not "
                  "appear in the plan at all. Prefer for_each whenever the collection can change.",
        lab=24,
    ),
]

def _anchor_tail(eyebrow: str) -> str:
    """Slug of the part of the eyebrow after the lab number, e.g. 'Keys and locking'."""
    tail = eyebrow.split("&middot;")[-1].strip().lower()
    return "".join(ch if ch.isalnum() else "-" for ch in tail).strip("-")


def build_anchors(topics: list[dict]) -> list[str]:
    """A stable id per topic, in page order.

    A lab with one topic uses its lab slug, so the anchor reads
    #lab13-multi-provider. A lab with several (lab00 has two) disambiguates with
    the eyebrow tail: #lab00-foundations, #lab00-authentication.
    """
    counts: dict[int, int] = {}
    for spec in topics:
        counts[spec["lab"]] = counts.get(spec["lab"], 0) + 1

    anchors = []
    for spec in topics:
        num = spec["lab"]
        if counts[num] == 1:
            anchors.append(lab_by_num(num)[1])
        else:
            anchors.append(f"lab{num:02d}-{_anchor_tail(spec['eyebrow'])}")
    if len(set(anchors)) != len(anchors):
        raise ValueError(f"duplicate topic anchors: {anchors}")
    return anchors


def check_topic_order(topics: list[dict]) -> None:
    """Page order is lab order. Nothing re-sorts at render time, so assert it here."""
    nums = [spec["lab"] for spec in topics]
    if nums != sorted(nums):
        raise ValueError(f"TOPICS is not in ascending lab order: {nums}")
    known = {lab[0] for lab in LABS}
    unknown = sorted(set(nums) - known)
    if unknown:
        raise ValueError(f"TOPICS references labs not in LABS: {unknown}")
    uncovered = sorted(known - set(nums))
    if uncovered:
        raise ValueError(f"labs with no topic card: {uncovered}")


CONCEPTS_CSS = """
/* Wide screens: topic index is a real sidebar column beside the content, so the two
   never overlap. The column itself is sticky and scrolls independently of the page. */
.concepts-layout {
    display: grid; grid-template-columns: 268px minmax(0, 1fr);
    gap: 20px; align-items: start;
}
.concepts-main { min-width: 0; }
.topicnav {
    position: sticky; top: 16px; max-height: calc(100vh - 32px);
    display: flex; flex-direction: column;
    background: #fff; border: 1px solid var(--slate-200); border-radius: 14px;
    padding: 12px 14px; box-shadow: 0 2px 12px rgba(15, 23, 42, 0.06);
}
.topicnav h2 { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em;
               color: var(--slate-500); margin-bottom: 8px; }
.topicnav .topiclist { overflow-y: auto; overscroll-behavior: contain; }
.topiclist { list-style: none; display: grid; gap: 4px; }
.topiclist a {
    display: block; padding: 5px 9px; border-radius: 8px; text-decoration: none;
    font-size: 0.78rem; line-height: 1.35; color: var(--slate-700); background: #f8fbff;
    border: 1px solid rgba(37, 99, 235, 0.12);
}
.topiclist a:hover { background: var(--blue); color: #fff; border-color: var(--blue); }
.topiclist a b { color: var(--blue); font-family: "SF Mono", Menlo, monospace;
                 font-size: 0.74rem; margin-right: 6px; }
.topiclist a:hover b { color: #fff; }
/* narrow-screen disclosure and its jump-back pill: off entirely on wide screens */
.topicnav-mobile, .topicfab { display: none; }
/* nothing is pinned above the content, so an anchor jump needs only breathing room */
.card[id] { scroll-margin-top: 18px; }
#topic-index { scroll-margin-top: 12px; }

@media (max-width: 1100px) {
    .concepts-layout { grid-template-columns: minmax(0, 1fr); }
    .topicnav { display: none; }
    .topicnav-mobile {
        display: block; background: #fff; border: 1px solid var(--slate-200);
        border-radius: 12px; box-shadow: 0 2px 12px rgba(15, 23, 42, 0.05);
    }
    .topicnav-mobile summary {
        cursor: pointer; padding: 9px 12px; font-size: 0.82rem; font-weight: 700;
        color: var(--blue);
    }
    .topicnav-mobile[open] summary { border-bottom: 1px solid var(--slate-200); }
    .topicnav-mobile .topiclist {
        grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
        padding: 10px 12px; max-height: 60vh; overflow-y: auto;
        overscroll-behavior: contain;
    }
    .topicfab {
        display: block; position: fixed; right: 14px; bottom: 14px; z-index: 30;
        padding: 9px 14px; border-radius: 999px; background: var(--blue); color: #fff;
        font-size: 0.78rem; font-weight: 800; text-decoration: none;
        box-shadow: 0 6px 18px rgba(37, 99, 235, 0.35);
    }
}
"""


def render_topic_nav(topics: list[dict], anchors: list[str], *, indent: str) -> str:
    """The 26 topic links as an <ol>. Rendered twice: sidebar and narrow-screen details."""
    items = []
    for spec, anchor in zip(topics, anchors):
        title = spec["heading"].replace('"', "&quot;")
        tail = spec["eyebrow"].split("&middot;")[-1].strip()
        items.append(
            f'{indent}    <li><a href="#{anchor}" title="{title}">'
            f'<b>lab{spec["lab"]:02d}</b>{tail}</a></li>'
        )
    return (f'{indent}<ol class="topiclist">\n'
            + "\n".join(items)
            + f"\n{indent}</ol>")


def render_concepts() -> str:
    """One page, every topic, lab00 to lab24. No tier grouping and no tier headings."""
    check_topic_order(TOPICS)
    anchors = build_anchors(TOPICS)

    intro = f"""        <div class="card">
            <span class="eyebrow">lab00 &ndash; lab24 &middot; one continuous sequence</span>
            <h2>Terraform concepts, in the order the labs teach them</h2>
            <p class="concept">Every topic in the track is on this page, ordered by lab number
                from your first <code class="inline">terraform init</code> to
                <code class="inline">count</code> versus
                <code class="inline">for_each</code> on real S3 buckets. Each card gives the
                concept in plain English, a real example, every significant line explained, and a
                link to the lab that practises it. Read straight down, or jump with the topic
                index &mdash; the sidebar on a wide screen, the collapsible list at the top of
                the page on a narrow one.</p>
            <div class="note">Starting from zero? Read
                <a href="terraform-101.html">Terraform 101</a> first &mdash; what Terraform is,
                HCL, providers, version constraints, state, and drift &mdash; then the
                <a href="aws-primer.html">AWS primer</a> for regions, VPCs, subnets, gateways,
                and security groups. The <a href="index.html">track home</a> has the searchable
                catalogue of all {len(LABS)} lab manuals.</div>
        </div>
"""

    cards = [intro]
    for spec, anchor in zip(TOPICS, anchors):
        href, label = practises(spec["lab"])
        cards.append(topic(
            spec["eyebrow"], spec["heading"], spec["concept"], spec["code"],
            spec["rows"], href, label, lang_note=spec.get("lang_note", ""),
            anchor=anchor,
        ))

    nav_title = f"All {len(TOPICS)} topics &mdash; lab00 to lab24"
    body = f"""        <div class="concepts-layout">
            <nav class="topicnav" aria-label="Topic index">
                <h2>{nav_title}</h2>
{render_topic_nav(TOPICS, anchors, indent=" " * 16)}
            </nav>
            <details class="topicnav-mobile" id="topic-index">
                <summary>{nav_title}</summary>
{render_topic_nav(TOPICS, anchors, indent=" " * 16)}
            </details>
            <div class="concepts-main">
{"".join(cards)}            </div>
        </div>
        <a class="topicfab" href="#topic-index">&#9776; Topics</a>
"""

    return page(
        "Terraform &mdash; Concepts",
        f"{len(TOPICS)} topics across all {len(LABS)} labs, in lab order. Each one: what it is, "
        "a real example, every significant line explained, and the lab that practises it.",
        body,
        active="concepts",
        stats=[f"{len(TOPICS)} topics", f"{len(LABS)} labs", "lab00&ndash;lab24", TF_FLOOR,
               AWS_PIN, "Region us-east-2"],
        extra_css=CONCEPTS_CSS,
    )


INDEX_CSS = """
.search-bar { margin: 4px 0 14px; }
.search-bar input {
    width: 100%; max-width: 480px; padding: 10px 14px; font-family: inherit;
    font-size: 0.92rem; color: var(--slate-900); background: #f8fafc;
    border: 1px solid var(--slate-200); border-radius: 10px; outline: none;
}
.search-bar input:focus { border-color: var(--blue); box-shadow: 0 0 0 3px rgba(37,99,235,0.12); }
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
@media (max-width: 768px) { .seq { grid-template-columns: 1fr; } }
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
    # First topic anchor per lab, so every catalog row deep-links into concepts.html.
    anchors = build_anchors(TOPICS)
    first_anchor: dict[int, str] = {}
    for spec, anchor in zip(TOPICS, anchors):
        first_anchor.setdefault(spec["lab"], anchor)

    rows = []
    for num, slug, title, tier, topic_text in LABS:
        rows.append(
            f'                    <tr>'
            f'<td class="lineref">lab{num:02d}</td>'
            f'<td><a href="../labmanuals/{slug}.md">{title}</a></td>'
            f'<td><span class="tag {tier}">{TIERS[tier]["label"]}</span></td>'
            f"<td>{topic_text}</td>"
            f'<td><a href="concepts.html#{first_anchor[num]}">lab{num:02d} concepts</a></td>'
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
                        diagram of what Lab 10 builds.</p>
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
                <a href="concepts.html">concepts page</a> or to
                <a href="{lab00_href}">Lab 00</a>.</div>
        </div>

        <div class="card">
            <span class="eyebrow">All {len(TOPICS)} topics on one page</span>
            <h2><a class="backlink" href="concepts.html">Terraform concepts &rarr;</a></h2>
            <p class="concept">One page, lab00 to lab24, in lab order &mdash; no tier pages and
                no tier navigation. Each topic gives the concept in plain English, a real HCL
                example, every significant line explained, and a link to the lab that practises
                it. A sticky topic index at the top jumps to any of the {len(TOPICS)} cards, and
                the Concepts column in the table below deep-links to the topic for each lab.</p>
            <p class="concept">Tier is still recorded per lab, in the Tier column below:
                <span class="tag basic">Basic</span> lab00&ndash;lab05,
                <span class="tag intermediate">Intermediate</span> lab06&ndash;lab12,
                <span class="tag advanced">Advanced</span> lab13&ndash;lab24. It tells you how
                much a lab assumes; it is not a place to navigate to.</p>
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
            <p class="concept">Four self-contained pages. No CDN, no external fonts, no build step
                &mdash; open any of them offline, or print them.</p>
            <table>
                <thead><tr><th style="width:22%;">Page</th><th style="width:14%;">Read it</th><th>Contents</th></tr></thead>
                <tbody>
                <tr><td class="lineref"><a href="terraform-101.html">terraform-101.html</a></td><td><strong>1st</strong></td><td>Terraform fundamentals from absolute zero: the tool, HCL, providers, version constraints, the CLI, state, drift.</td></tr>
                <tr><td class="lineref"><a href="aws-primer.html">aws-primer.html</a></td><td><strong>2nd</strong></td><td>AWS concepts from absolute zero, each with its Terraform resource type, plus the capstone architecture diagram.</td></tr>
                <tr><td class="lineref"><a href="concepts.html">concepts.html</a></td><td>alongside every lab</td><td>All {len(TOPICS)} topics, lab00 to lab24, in one continuous sequence with a sticky topic index.</td></tr>
                <tr><td class="lineref">index.html</td><td>as needed</td><td>This page: the entry-point sequence and the searchable table of all {len(LABS)} labs.</td></tr>
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
                <tr><td class="lineref">docs/</td><td>Longer written deep dives, one flat numbered file per subject, for after the lab.</td></tr>
                </tbody>
            </table>
            <div class="warn">Every AWS lab costs money while it is running. Finish with
                <code class="inline">terraform destroy</code>, every time.</div>
        </div>
{INDEX_JS}"""

    return page(
        "Terraform Track",
        f"{len(LABS)} labs, lab00 to lab24 &mdash; from your first "
        "<code class=\"inline\">terraform init</code> to a working public web server built "
        "entirely in code.",
        body,
        active="index",
        stats=[f"{len(LABS)} labs", f"{len(TOPICS)} topics", f"{len(HTML_PAGES)} HTML pages",
               TF_FLOOR, AWS_PIN, "Region us-east-2", "Offline"],
        extra_css=INDEX_CSS,
    )


def write(name: str, content: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")
    print(f"  {len(content.splitlines()):5d} lines  {path.relative_to(ROOT)}")


# Manuals still being authored. Their hrefs are generated deliberately; report them as
# pending rather than missing, and remove each slug once its file lands.
PENDING_MANUALS: set[str] = set()


def check_hrefs() -> int:
    """Every ../labmanuals/labNN-*.md href must resolve to a real file."""
    missing = []
    pending = []
    for num, slug, _title, _tier, _topic in LABS:
        target = ROOT / "terraform" / "labmanuals" / f"{slug}.md"
        if target.exists():
            continue
        entry = f"lab{num:02d}: {target.relative_to(ROOT)}"
        (pending if slug in PENDING_MANUALS else missing).append(entry)
    if pending:
        print("\nPENDING lab manuals (expected, still being written):")
        for item in pending:
            print(f"  {item}")
    if missing:
        print("\nMISSING lab manuals referenced by generated hrefs:")
        for item in missing:
            print(f"  {item}")
    elif pending:
        print(f"\nhref check: {len(LABS) - len(pending)} of {len(LABS)} lab manual targets exist; "
              f"{len(pending)} pending.")
    else:
        print(f"\nhref check: all {len(LABS)} lab manual targets exist.")
    return len(missing)


RETIRED_PAGES = ("basic.html", "intermediate.html", "advanced.html")


def check_page_set() -> int:
    """No generated page may link to a Terraform HTML page outside the four-page set."""
    import re

    bad = 0
    for name in OWNED_PAGES:
        text = (OUT_DIR / name).read_text(encoding="utf-8")
        for href in re.findall(r'href="\.?/?([a-z0-9._-]+\.html)(?:#[a-z0-9._-]+)?"', text):
            if href not in HTML_PAGES:
                print(f"  OFF-SET LINK {name} -> {href}")
                bad += 1
            elif not (OUT_DIR / href).exists():
                print(f"  MISSING PAGE {name} -> {href}")
                bad += 1
        for retired in RETIRED_PAGES:
            if retired in text:
                print(f"  RETIRED TIER PAGE still named in {name}: {retired}")
                bad += 1
    if not bad:
        print(f"page-set check: every HTML link stays inside the {len(HTML_PAGES)}-page set "
              "and resolves on disk; no tier page is referenced.")
    return bad


def check_anchors() -> int:
    """Every #anchor in the generated pages must resolve to an id on concepts.html."""
    import re

    ids = set(re.findall(r'<div class="card" id="([a-z0-9-]+)">',
                         (OUT_DIR / "concepts.html").read_text(encoding="utf-8")))
    expected = set(build_anchors(TOPICS))
    bad = 0
    if ids != expected:
        print(f"  ANCHOR IDS MISMATCH: missing {sorted(expected - ids)}, "
              f"extra {sorted(ids - expected)}")
        bad += 1

    # every id on concepts.html, not just the topic cards: the topic index itself is a
    # link target, so a bare #anchor may resolve to a card or to a page control.
    concepts_ids = set(re.findall(
        r' id="([a-z0-9-]+)"', (OUT_DIR / "concepts.html").read_text(encoding="utf-8")))
    for name in OWNED_PAGES:
        text = (OUT_DIR / name).read_text(encoding="utf-8")
        resolvable = concepts_ids | set(re.findall(r' id="([a-z0-9-]+)"', text))
        for target in re.findall(r'href="(?:concepts\.html)?#([a-z0-9-]+)"', text):
            if target not in resolvable:
                print(f"  DANGLING ANCHOR {name} -> #{target}")
                bad += 1

    nav_targets = set(re.findall(
        r'<li><a href="#([a-z0-9-]+)"',
        (OUT_DIR / "concepts.html").read_text(encoding="utf-8")))
    if nav_targets != ids:
        print(f"  TOPIC NAV INCOMPLETE: nav lists {len(nav_targets)} of {len(ids)} topics")
        bad += 1

    if not bad:
        print(f"anchor check: {len(ids)} topic ids on concepts.html, the topic index lists all "
              "of them, and every in-page link resolves.")
    return bad


def remove_retired_pages() -> None:
    """basic/intermediate/advanced.html are superseded by concepts.html."""
    for name in RETIRED_PAGES:
        path = OUT_DIR / name
        if path.exists():
            path.unlink()
            print(f"  removed superseded {path.relative_to(ROOT)}")


def main() -> None:
    print("Generating Terraform track HTML:")
    write("concepts.html", render_concepts())
    write("index.html", render_index())
    remove_retired_pages()
    check_hrefs()
    check_page_set()
    check_anchors()


if __name__ == "__main__":
    main()
