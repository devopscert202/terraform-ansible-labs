"""Topic page content — part 1: Terraform essentials."""
from html_helpers import cards_html, examples_html, flow_html, practice_html, table_html

TF_SVG_FOUNDATIONS = """
            <svg viewBox="0 0 950 380" style="width:100%;max-width:950px;margin:20px auto;display:block;">
                <text x="475" y="28" text-anchor="middle" font-size="18" font-weight="bold" fill="#1e293b">Terraform Core Execution Model</text>
                <rect x="40" y="60" width="180" height="70" rx="8" fill="#ede4f7" stroke="#7B42BC" stroke-width="2"/>
                <text x="130" y="88" text-anchor="middle" font-size="13" font-weight="bold" fill="#5c2d94">Configuration</text>
                <text x="130" y="108" text-anchor="middle" font-size="10" fill="#5c2d94" font-family="monospace">*.tf, *.tfvars</text>
                <line x1="220" y1="95" x2="280" y2="95" stroke="#7B42BC" stroke-width="2" marker-end="url(#tf1)"/>
                <rect x="280" y="55" width="160" height="80" rx="10" fill="#f8fafc" stroke="#7B42BC" stroke-width="3"/>
                <text x="360" y="85" text-anchor="middle" font-size="14" font-weight="bold" fill="#5c2d94">Terraform CLI</text>
                <text x="360" y="105" text-anchor="middle" font-size="10" fill="#64748b">init · plan · apply</text>
                <line x1="440" y1="95" x2="500" y2="95" stroke="#7B42BC" stroke-width="2" marker-end="url(#tf1)"/>
                <rect x="500" y="55" width="180" height="80" rx="8" fill="#dbeafe" stroke="#3b82f6" stroke-width="2"/>
                <text x="590" y="85" text-anchor="middle" font-size="13" font-weight="bold" fill="#1e40af">Providers</text>
                <text x="590" y="105" text-anchor="middle" font-size="10" fill="#1e3a8a" font-family="monospace">aws, random, ...</text>
                <line x1="680" y1="95" x2="740" y2="95" stroke="#3b82f6" stroke-width="2" marker-end="url(#tf2)"/>
                <rect x="740" y="55" width="170" height="80" rx="8" fill="#dcfce7" stroke="#22c55e" stroke-width="2"/>
                <text x="825" y="85" text-anchor="middle" font-size="13" font-weight="bold" fill="#166534">Cloud APIs</text>
                <text x="825" y="105" text-anchor="middle" font-size="10" fill="#14532d">EC2, VPC, IAM...</text>
                <rect x="280" y="180" width="200" height="70" rx="8" fill="#fef3c7" stroke="#f59e0b" stroke-width="2"/>
                <text x="380" y="210" text-anchor="middle" font-size="13" font-weight="bold" fill="#92400e">State File</text>
                <text x="380" y="230" text-anchor="middle" font-size="10" fill="#78350f" font-family="monospace">terraform.tfstate</text>
                <line x1="380" y1="135" x2="380" y2="180" stroke="#f59e0b" stroke-width="2" marker-end="url(#tf3)"/>
                <rect x="40" y="280" width="870" height="80" rx="8" fill="#faf5ff" stroke="#a855f7" stroke-width="2"/>
                <text x="475" y="310" text-anchor="middle" font-size="13" font-weight="bold" fill="#7e22ce">Lab 01 — terraform/essentials/labs/lab01-providers-init/</text>
                <text x="475" y="335" text-anchor="middle" font-size="11" fill="#6b21a8">terraform init → terraform validate → (optional) terraform apply</text>
                <defs>
                    <marker id="tf1" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#7B42BC"/></marker>
                    <marker id="tf2" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#3b82f6"/></marker>
                    <marker id="tf3" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#f59e0b"/></marker>
                </defs>
            </svg>"""

FOUNDATIONS = {
    "track": "terraform/essentials",
    "filename": "foundations.html",
    "page_title": "Terraform Foundations — Interactive Guide",
    "eyebrow": "Terraform Essentials",
    "h1": "Terraform Foundations",
    "subtitle": "Providers, resources, HCL syntax, and the init workflow that every lab depends on.",
    "lead": "Terraform is a declarative infrastructure-as-code tool. You describe <strong>desired state</strong> in HCL files; Terraform compares that to <strong>current state</strong> and proposes a plan of API calls to converge reality.",
    "tabs": [],
}

FOUNDATIONS["tabs"] = [
    {
        "id": "concept",
        "label": "Concept",
        "kicker": "Core Model",
        "title": "What Is Terraform?",
        "body": cards_html([
            ("Declarative IaC", "You write <code>resource \"aws_instance\" \"web\"</code> blocks describing what should exist. Terraform figures out create, update, or destroy operations."),
            ("Providers", "Plugins such as <code>hashicorp/aws</code> translate HCL into cloud API calls. Version constraints live in <code>required_providers</code>."),
            ("State", "Terraform stores a mapping between configuration addresses and real resource IDs in a state file. Without state, plans are unreliable."),
            ("Root module", "Every lab directory is a root module — a folder with <code>main.tf</code> (and friends) that Terraform runs as one unit."),
            ("Lock file", "<code>.terraform.lock.hcl</code> pins exact provider versions after <code>terraform init</code>. Commit it in team projects."),
            ("Credential chain", "Never put access keys in provider blocks. Use <code>AWS_PROFILE</code>, environment variables, or IAM roles."),
        ]) + '\n            <div class="section-note">Terraform Essentials Lab 01 uses only the Random provider for apply — AWS provider is declared for credential-chain practice.</div>',
    },
    {
        "id": "architecture",
        "label": "Architecture",
        "kicker": "Execution Model",
        "title": "How Terraform Talks to Cloud APIs",
        "body": examples_html([
            ("Lab directory layout", """terraform/essentials/labs/lab01-providers-init/
├── main.tf              # required_providers, provider, resources
├── .terraform/          # created by init (gitignored)
└── .terraform.lock.hcl  # provider version pins"""),
            ("required_providers block", """terraform {
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
}"""),
            ("Provider block (no secrets)", """provider "aws" {
  region = var.aws_region
  # Credentials from AWS_PROFILE / env / IAM role — never here
}"""),
        ], lab="<code>terraform/essentials/labs/lab01-providers-init/main.tf</code>") + TF_SVG_FOUNDATIONS,
    },
    {
        "id": "flow",
        "label": "Flow",
        "kicker": "First Run",
        "title": "Lab 01 Initialization Workflow",
        "body": flow_html([
            ("Verify toolchain", "<code>terraform version</code> — confirm Terraform 1.5+ before working with lab files."),
            ("Change to lab directory", "<code>cd terraform/essentials/labs/lab01-providers-init</code> — each lab is an isolated root module."),
            ("Inspect configuration", "Read <code>main.tf</code> — note <code>required_providers</code> and the <code>random_pet</code> resource."),
            ("Initialize", "<code>terraform init</code> downloads providers and writes <code>.terraform.lock.hcl</code>."),
            ("List providers", "<code>terraform providers</code> shows resolved provider sources and versions."),
            ("Validate", "<code>terraform validate</code> checks syntax and internal references — no cloud calls."),
            ("Optional apply", "<code>terraform apply</code> creates the random pet; <code>terraform destroy</code> cleans up."),
        ]) + '\n            <div class="section-note">See <a href="../labmanuals/lab01-providers-init.md">lab01-providers-init.md</a> for step-by-step validation criteria.</div>',
    },
    {
        "id": "setup",
        "label": "Setup",
        "kicker": "Install",
        "title": "Installing Terraform on Your Workstation",
        "body": examples_html([
            ("macOS — Homebrew", """brew tap hashicorp/tap
brew install hashicorp/tap/terraform
terraform version"""),
            ("Linux — HashiCorp apt repo", """wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
terraform version"""),
            ("Verify in lab directory", """cd terraform/essentials/labs/lab01-providers-init
terraform init
terraform validate"""),
            ("AWS credential check (optional)", """export AWS_PROFILE=your-lab-profile
aws sts get-caller-identity"""),
        ]),
    },
    {
        "id": "commands",
        "label": "Commands",
        "kicker": "Quick Reference",
        "title": "Essential Terraform Commands (Essentials Track)",
        "body": table_html(
            ["Category", "Command", "Description"],
            [
                ["Toolchain", "<code>terraform version</code>", "Print CLI and core version"],
                ["Init", "<code>terraform init</code>", "Download providers, init backend"],
                ["Init", "<code>terraform providers</code>", "List configured providers"],
                ["Quality", "<code>terraform fmt</code>", "Format HCL files recursively"],
                ["Quality", "<code>terraform validate</code>", "Validate configuration syntax"],
                ["Plan", "<code>terraform plan</code>", "Preview changes without applying"],
                ["Apply", "<code>terraform apply</code>", "Execute proposed changes"],
                ["Apply", "<code>terraform apply -auto-approve</code>", "Apply without interactive prompt"],
                ["Destroy", "<code>terraform destroy</code>", "Remove all managed resources"],
                ["State", "<code>terraform state list</code>", "List resources in state"],
                ["Output", "<code>terraform output</code>", "Show output values"],
            ],
        ),
    },
    {
        "id": "examples",
        "label": "Examples",
        "kicker": "Hands-On",
        "title": "Real Commands from Lab 01",
        "body": examples_html([
            ("Step 1.1 — Version check", """terraform version"""),
            ("Step 1.2 — Enter lab directory", """cd terraform/essentials/labs/lab01-providers-init
pwd"""),
            ("Step 3.1 — Initialize providers", """terraform init"""),
            ("Step 3.2 — Inspect lock file", """cat .terraform.lock.hcl | head -20"""),
            ("Step 3.3 — List providers", """terraform providers"""),
            ("Step 4.1 — Validate", """terraform validate"""),
            ("Step 5.1 — Optional apply", """terraform apply
# type yes when prompted"""),
            ("Step 5.2 — Optional destroy", """terraform destroy"""),
        ], lab="<code>terraform/essentials/labs/lab01-providers-init/</code> · manual: <code>labmanuals/lab01-providers-init.md</code>"),
    },
    {
        "id": "comparison",
        "label": "Compare",
        "kicker": "Decision Guide",
        "title": "Terraform vs Other IaC Approaches",
        "body": table_html(
            ["Aspect", "Terraform", "CloudFormation", "Ansible"],
            [
                ["Paradigm", "Declarative graph", "Declarative AWS-only", "Procedural tasks"],
                ["State", "Explicit state file", "AWS-managed stacks", "None (by default)"],
                ["Multi-cloud", "Yes — provider ecosystem", "AWS only", "Yes — agentless SSH/API"],
                ["Drift detection", "<code>terraform plan</code>", "Stack drift detection", "Ad hoc / check mode"],
                ["Learning curve", "Medium — HCL + state", "Medium — YAML/JSON", "Medium — YAML playbooks"],
                ["Best fit", "Infrastructure provisioning", "AWS-native teams", "Configuration management"],
            ],
        ) + '\n            <div class="section-note">This repository teaches both Terraform (provision) and Ansible (configure) — they complement each other in real pipelines.</div>',
    },
    {
        "id": "practice",
        "label": "Practice",
        "kicker": "Use It Well",
        "title": "Practice and Lab Links",
        "body": practice_html([
            ("Lab 01 — Providers", "Complete init and validate in <code>lab01-providers-init</code>. Identify every block type in <code>main.tf</code>.", "../labmanuals/lab01-providers-init.md"),
            ("Lab 02 — EC2", "Apply a real AWS EC2 instance. Observe how provider credentials flow from the environment.", "../labmanuals/lab02-ec2.md"),
            ("Fmt discipline", "Run <code>terraform fmt -recursive</code> before every commit in team projects.", "../labmanuals/lab04-fmt-validate.md"),
            ("Lock file hygiene", "Delete <code>.terraform/</code> and re-run init. Confirm lock file pins the same versions.", "../labmanuals/lab01-providers-init.md"),
            ("Validate before plan", "Break syntax intentionally, run validate, fix, and compare error messages.", "../labmanuals/lab04-fmt-validate.md"),
            ("Destroy cleanup", "Always destroy lab resources when finished to avoid AWS charges.", "../labmanuals/lab03-plan-apply-destroy.md"),
        ]),
    },
]
