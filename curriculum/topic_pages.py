"""Terraform + Ansible topic page definitions for build_k8s_style_html.py."""
from __future__ import annotations

from html_helpers import cards_html, examples_html, flow_html, practice_html, table_html

# Re-use foundations from part1
from topic_pages_part1 import FOUNDATIONS  # noqa: F401
from topic_pages_ansible import ANSIBLE_TOPICS


def _svg(title: str, boxes: list[tuple[int, int, int, int, str, str, str]], arrows: list[str] = "") -> str:
  """Generate simple pipeline SVG."""
  rects = []
  for x, y, w, h, fill, stroke, label in boxes:
    rects.append(
      f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
      f'<text x="{x+w//2}" y="{y+h//2}" text-anchor="middle" font-size="12" font-weight="bold" fill="#1e293b">{label}</text>'
    )
  return f"""
            <svg viewBox="0 0 950 320" style="width:100%;max-width:950px;margin:20px auto;display:block;">
                <text x="475" y="28" text-anchor="middle" font-size="18" font-weight="bold" fill="#1e293b">{title}</text>
                {''.join(rects)}
                {arrows}
            </svg>"""


def _tab(id_: str, label: str, kicker: str, title: str, body: str) -> dict:
  return {"id": id_, "label": label, "kicker": kicker, "title": title, "body": body}


def _meta(track: str, filename: str, page_title: str, eyebrow: str, h1: str, subtitle: str, lead: str, tabs: list) -> dict:
  return {
    "track": track,
    "filename": filename,
    "page_title": page_title,
    "eyebrow": eyebrow,
    "h1": h1,
    "subtitle": subtitle,
    "lead": lead,
    "tabs": tabs,
  }


def _pad_commands(commands: list[tuple[str, str, str]]) -> str:
  return table_html(["Category", "Command", "Description"], [[a, b, c] for a, b, c in commands])


def _extra_examples(title: str, blocks: list[str]) -> str:
  return examples_html([(f"{title} — example {i+1}", b) for i, b in enumerate(blocks)])


# ── Terraform Essentials: workflow ──────────────────────────────────────────

WORKFLOW = _meta(
  "terraform/essentials", "workflow.html",
  "Terraform Workflow — Interactive Guide", "Terraform Essentials",
  "Terraform Workflow", "Init, fmt, validate, plan, apply, and destroy — the daily operator loop.",
  "Every Terraform change follows the same <strong>read → plan → apply</strong> rhythm. Labs 03–04 drill this until it becomes muscle memory.",
  [
    _tab("concept", "Concept", "Core Model", "The Terraform Operator Loop",
         cards_html([
           ("Write", "Edit <code>*.tf</code> files describing desired infrastructure."),
           ("Format", "<code>terraform fmt</code> normalizes HCL style — run before every commit."),
           ("Validate", "<code>terraform validate</code> catches syntax and reference errors locally."),
           ("Plan", "<code>terraform plan</code> shows create/update/destroy actions with diffs."),
           ("Review", "Human or CI approves the plan output before any cloud mutation."),
           ("Apply", "<code>terraform apply</code> executes the approved graph."),
           ("Destroy", "<code>terraform destroy</code> tears down all managed resources in the root module."),
         ])),
    _tab("architecture", "Architecture", "Plan Graph", "What Happens During Plan",
         examples_html([
           ("Lab 03 directory", "terraform/essentials/labs/lab03-plan-apply-destroy/\n├── main.tf\n├── variables.tf\n└── outputs.tf"),
           ("Plan output anatomy", "# aws_instance.web will be created\n  + resource \"aws_instance\" \"web\" {\n      + ami           = \"ami-0c55b159cbfafe1f0\"\n      + instance_type = \"t3.micro\"\n    }\n\nPlan: 1 to add, 0 to change, 0 to destroy."),
         ], lab="<code>terraform/essentials/labs/lab03-plan-apply-destroy/</code>")
         + _svg("Plan → Apply Pipeline", [
           (40, 70, 150, 60, "#dbeafe", "#326CE5", "HCL Config"),
           (230, 70, 150, 60, "#dbeafe", "#3b82f6", "terraform plan"),
           (420, 70, 150, 60, "#fef3c7", "#f59e0b", "Review"),
           (610, 70, 150, 60, "#dcfce7", "#22c55e", "terraform apply"),
           (800, 70, 120, 60, "#f0fdf4", "#16a34a", "AWS API"),
         ])),
    _tab("flow", "Flow", "Lab 03", "Plan, Apply, Destroy Lifecycle",
         flow_html([
           ("cd lab03", "<code>cd terraform/essentials/labs/lab03-plan-apply-destroy</code>"),
           ("init", "<code>terraform init</code> if not already initialized."),
           ("plan", "<code>terraform plan -out=tfplan</code> saves the plan to a file."),
           ("review", "Read the plan: count adds/changes/destroys. Confirm instance type and AMI."),
           ("apply saved plan", "<code>terraform apply tfplan</code> — applies exactly what was planned."),
           ("verify", "<code>terraform show</code> or AWS console — confirm resource exists."),
           ("destroy", "<code>terraform destroy</code> — remove all resources when lab is done."),
         ])),
    _tab("setup", "Setup", "Quality Gates", "Fmt and Validate Before Plan",
         examples_html([
           ("Lab 04 — fmt and validate", "cd terraform/essentials/labs/lab04-fmt-validate\nterraform fmt -recursive\nterraform validate"),
           ("Check formatting diff", "terraform fmt -check -recursive\n# non-zero exit if files need formatting"),
           ("CI-style sequence", "terraform init -input=false\nterraform fmt -check -recursive\nterraform validate\nterraform plan -input=false -out=tfplan"),
         ])),
    _tab("commands", "Commands", "Quick Reference", "Workflow Commands",
         _pad_commands([
           ("Init", "<code>terraform init</code>", "Prepare working directory"),
           ("Fmt", "<code>terraform fmt -recursive</code>", "Format all HCL in tree"),
           ("Validate", "<code>terraform validate</code>", "Static configuration check"),
           ("Plan", "<code>terraform plan</code>", "Preview changes"),
           ("Plan file", "<code>terraform plan -out=tfplan</code>", "Save plan for apply"),
           ("Apply", "<code>terraform apply</code>", "Execute changes"),
           ("Apply file", "<code>terraform apply tfplan</code>", "Apply saved plan only"),
           ("Show", "<code>terraform show</code>", "Inspect current state/resources"),
           ("Destroy", "<code>terraform destroy</code>", "Remove all managed resources"),
           ("Graph", "<code>terraform graph</code>", "Dependency graph (DOT format)"),
         ])),
    _tab("examples", "Examples", "Hands-On", "Lab 03 Real Commands",
         examples_html([
           ("Enter lab", "cd terraform/essentials/labs/lab03-plan-apply-destroy"),
           ("Initialize", "terraform init"),
           ("Plan", "terraform plan"),
           ("Apply", "terraform apply"),
           ("Show state", "terraform state list"),
           ("Destroy", "terraform destroy -auto-approve"),
         ], lab="labmanuals/lab03-plan-apply-destroy.md")
         + _extra_examples("Workflow drills", [
           "terraform plan -var='instance_type=t3.small'",
           "terraform apply -target=aws_instance.web",
           "terraform refresh",
         ])),
    _tab("comparison", "Compare", "Decision Guide", "Plan Review Strategies",
         table_html(["Approach", "Pros", "Cons", "When"],
           [["Interactive apply", "Simple for labs", "No audit trail", "Learning environments"],
            ["Saved plan file", "Plan matches apply exactly", "Extra step", "CI/CD pipelines"],
            ["-auto-approve", "Fast automation", "Dangerous in prod", "Ephemeral test envs only"],
            ["-target", "Surgical changes", "Can cause drift", "Emergency fixes only"]]
         )),
    _tab("practice", "Practice", "Use It Well", "Workflow Practice Cards",
         practice_html([
           ("Lab 03", "Complete full plan/apply/destroy cycle. Save a plan file and apply it.", "../labmanuals/lab03-plan-apply-destroy.md"),
           ("Lab 04", "Run fmt -check in CI style. Fix formatting issues.", "../labmanuals/lab04-fmt-validate.md"),
           ("Plan literacy", "Identify every symbol (+ ~ -) in a plan before typing yes.", "../labmanuals/lab03-plan-apply-destroy.md"),
           ("Destroy discipline", "Never leave EC2 instances running overnight in shared accounts.", "../labmanuals/lab03-plan-apply-destroy.md"),
           ("Target caution", "Use -target only when you understand dependency side effects.", "../labmanuals/lab03-plan-apply-destroy.md"),
           ("Graph viz", "Pipe terraform graph to dot for visual dependency understanding.", "../labmanuals/lab04-fmt-validate.md"),
         ])),
  ],
)

# Continue with more topics - I'll add them all in this file
# Due to size, using a builder for remaining similar topics

def _tf_essentials_variables():
  return _meta("terraform/essentials", "variables.html", "Terraform Variables — Interactive Guide",
    "Terraform Essentials", "Variables & Outputs", "Input variables, outputs, types, validation, and tfvars secrets hygiene.",
    "Variables parameterize modules without editing source. Outputs expose values to humans, CI, and other Terraform configurations.",
    [
      _tab("concept", "Concept", "Core Model", "Variables and Outputs",
           cards_html([
             ("Input variables", "Declared with <code>variable</code> blocks; set via CLI, env, or <code>*.tfvars</code>."),
             ("Types", "string, number, bool, list, map, object — type constraints catch mistakes early."),
             ("Defaults", "Optional defaults make modules easier to consume; required vars force explicit choices."),
             ("Sensitive", "<code>sensitive = true</code> redacts values in CLI output and logs."),
             ("Outputs", "<code>output</code> blocks export values after apply — IPs, ARNs, connection strings."),
             ("tfvars files", "<code>terraform.tfvars</code> and <code>*.auto.tfvars</code> load automatically; never commit secrets."),
           ])),
      _tab("architecture", "Architecture", "Data Flow", "How Values Reach Resources",
           examples_html([
             ("variables.tf", 'variable "instance_type" {\n  type        = string\n  default     = "t3.micro"\n  description = "EC2 instance size"\n}'),
             ("main.tf usage", 'resource "aws_instance" "web" {\n  instance_type = var.instance_type\n}'),
             ("outputs.tf", 'output "public_ip" {\n  value = aws_instance.web.public_ip\n}'),
           ], lab="terraform/essentials/labs/lab05-variables/")
           + _svg("Variable Resolution", [
             (30, 80, 140, 55, "#dbeafe", "#326CE5", "tfvars"),
             (200, 80, 140, 55, "#dbeafe", "#3b82f6", "-var flags"),
             (370, 80, 140, 55, "#fef3c7", "#f59e0b", "TF_VAR_*"),
             (540, 80, 180, 55, "#dcfce7", "#22c55e", "var.* in HCL"),
           ])),
      _tab("flow", "Flow", "Lab 05", "Variable Override Workflow",
           flow_html([
             ("cd lab05", "cd terraform/essentials/labs/lab05-variables"),
             ("init", "terraform init"),
             ("plan defaults", "terraform plan — observe default variable values in plan output."),
             ("override CLI", "terraform plan -var='instance_type=t3.small'"),
             ("tfvars file", "echo 'instance_type = \"t3.nano\"' > dev.tfvars && terraform plan -var-file=dev.tfvars"),
             ("apply", "terraform apply -var-file=dev.tfvars"),
             ("outputs", "terraform output"),
             ("destroy", "terraform destroy"),
           ])),
      _tab("setup", "Setup", "Secrets", "tfvars and Lab 08 Secrets",
           examples_html([
             ("dev.tfvars (gitignored pattern)", 'instance_type = "t3.micro"\naws_region    = "us-east-1"'),
             ("Lab 08 — sensitive outputs", "cd terraform/essentials/labs/lab08-tfvars-secrets\nterraform plan -var-file=secrets.tfvars"),
             ("Never commit", "# .gitignore\n*.tfvars\n!example.tfvars\n.terraform/\nterraform.tfstate*"),
           ])),
      _tab("commands", "Commands", "Quick Reference", "Variable Commands",
           _pad_commands([
             ("Plan var", "<code>terraform plan -var='key=val'</code>", "Inline override"),
             ("Var file", "<code>terraform plan -var-file=dev.tfvars</code>", "Load tfvars file"),
             ("Env var", "<code>TF_VAR_instance_type=t3.small terraform plan</code>", "Environment override"),
             ("Output", "<code>terraform output</code>", "Show all outputs"),
             ("Output one", "<code>terraform output -raw public_ip</code>", "Single raw value"),
             ("Console", "<code>terraform console</code>", "Evaluate expressions"),
           ])),
      _tab("examples", "Examples", "Hands-On", "Lab 05 and Lab 08 Commands",
           examples_html([
             ("Lab 05 plan", "cd terraform/essentials/labs/lab05-variables\nterraform init\nterraform plan"),
             ("Override type", "terraform apply -var='instance_type=t3.small'"),
             ("Read output", "terraform output instance_public_ip"),
             ("Lab 08 secrets", "cd terraform/essentials/labs/lab08-tfvars-secrets\nterraform plan -var-file=secrets.tfvars"),
           ], lab="lab05-variables/ · lab08-tfvars-secrets/")),
      _tab("comparison", "Compare", "Decision Guide", "Variable Precedence",
           table_html(["Priority (high→low)", "Source", "Example"],
             [["1", "CLI -var", "-var='instance_type=t3.large'"],
              ["2", "CLI -var-file", "-var-file=prod.tfvars"],
              ["3", "TF_VAR_* env", "TF_VAR_instance_type=t3.small"],
              ["4", "terraform.tfvars", "Auto-loaded in directory"],
              ["5", "variable default", "default = \"t3.micro\""]])),
      _tab("practice", "Practice", "Use It Well", "Variable Practice",
           practice_html([
             ("Lab 05", "Try every override method and compare plan output.", "../labmanuals/lab05-variables.md"),
             ("Lab 08", "Use sensitive variables and confirm redaction in output.", "../labmanuals/lab08-tfvars-secrets.md"),
             ("Type errors", "Set wrong type intentionally; read validate error.", "../labmanuals/lab05-variables.md"),
             ("Output chaining", "Reference one output when writing another module consumer.", "../labmanuals/lab05-variables.md"),
             ("tfvars hygiene", "Create example.tfvars with dummy values for teammates.", "../labmanuals/lab08-tfvars-secrets.md"),
             ("Console expr", "Use terraform console to test length() and lookup() on maps.", "../labmanuals/lab05-variables.md"),
           ])),
    ])

VARIABLES = _tf_essentials_variables()

STATE_ESS = _meta("terraform/essentials", "state.html", "Terraform State — Interactive Guide",
  "Terraform Essentials", "Local State", "What state contains, why it matters, and local state operations in Lab 06.",
  "State is Terraform's memory. It maps <code>aws_instance.web</code> in HCL to <code>i-0abc123</code> in AWS — without it, Terraform cannot plan updates safely.",
  [
    _tab("concept", "Concept", "Core Model", "Understanding State",
         cards_html([
           ("Resource mapping", "Links configuration addresses to real cloud resource IDs."),
           ("Metadata", "Stores dependency info, serial numbers, and sometimes sensitive attributes."),
           ("Local default", "<code>terraform.tfstate</code> lives in the working directory — fine for solo labs."),
           ("Never edit casually", "Manual state surgery is for experts; prefer import and refresh."),
           ("Gitignore", "State often contains secrets — add <code>terraform.tfstate*</code> to .gitignore."),
           ("State commands", "<code>state list</code>, <code>state show</code>, <code>state mv</code> for operations."),
         ])),
    _tab("architecture", "Architecture", "State File", "State JSON Structure",
         examples_html([
           ("State list", "terraform state list\n# aws_instance.web\n# aws_security_group.web"),
           ("State show", "terraform state show aws_instance.web"),
           ("Lab 06 directory", "terraform/essentials/labs/lab06-local-state/"),
         ], lab="lab06-local-state/")
         + _svg("State Read/Write Cycle", [
           (50, 80, 160, 60, "#fef3c7", "#f59e0b", "Read State"),
           (250, 80, 160, 60, "#dbeafe", "#3b82f6", "Build Graph"),
           (450, 80, 160, 60, "#dbeafe", "#326CE5", "Call APIs"),
           (650, 80, 200, 60, "#dcfce7", "#22c55e", "Write State"),
         ])),
    _tab("flow", "Flow", "Lab 06", "Local State Lab Flow",
         flow_html([
           ("cd lab06", "cd terraform/essentials/labs/lab06-local-state"),
           ("apply", "terraform apply — creates resources and writes terraform.tfstate"),
           ("inspect file", "cat terraform.tfstate | jq '.resources[0].type'"),
           ("state list", "terraform state list"),
           ("state show", "terraform state show aws_instance.web"),
           ("refresh", "terraform apply -refresh-only"),
           ("destroy", "terraform destroy"),
         ])),
    _tab("setup", "Setup", "Hygiene", "State Safety Practices",
         examples_html([
           (".gitignore", "terraform.tfstate\nterraform.tfstate.backup\n.terraform/\n*.tfvars"),
           ("Backup before risky ops", "cp terraform.tfstate terraform.tfstate.backup.manual"),
           ("Sensitive output", 'output "db_password" {\n  value     = random_password.db.result\n  sensitive = true\n}'),
         ])),
    _tab("commands", "Commands", "Quick Reference", "State Commands",
         _pad_commands([
           ("List", "<code>terraform state list</code>", "All resource addresses"),
           ("Show", "<code>terraform state show ADDR</code>", "One resource detail"),
           ("Mv", "<code>terraform state mv SRC DST</code>", "Rename without recreate"),
           ("Rm", "<code>terraform state rm ADDR</code>", "Remove from state only"),
           ("Pull", "<code>terraform state pull</code>", "Print state JSON"),
           ("Push", "<code>terraform state push</code>", "Upload state (dangerous)"),
           ("Refresh", "<code>terraform apply -refresh-only</code>", "Sync state with real infra"),
         ])),
    _tab("examples", "Examples", "Hands-On", "Lab 06 Commands",
         examples_html([
           ("Apply and inspect", "cd terraform/essentials/labs/lab06-local-state\nterraform apply\nterraform state list"),
           ("Show resource", "terraform state show aws_instance.web"),
           ("Remove from state", "# advanced — terraform state rm aws_instance.web"),
         ], lab="lab06-local-state/")),
    _tab("comparison", "Compare", "Decision Guide", "Local vs Remote State",
         table_html(["Aspect", "Local", "Remote (S3)"],
           [["Collaboration", "Single machine", "Team + CI"],
            ["Locking", "None", "S3 native / DynamoDB"],
            ["Backup", "Manual", "S3 versioning"],
            ["Risk", "Lost laptop", "IAM misconfiguration"],
            ["Lab", "Lab 06", "Extended track Lab 07+"]]
         )),
    _tab("practice", "Practice", "Use It Well", "State Practice",
         practice_html([
           ("Lab 06", "Apply, inspect state JSON, list and show resources.", "../labmanuals/lab06-local-state.md"),
           ("Refresh-only", "Change a tag in AWS console; run refresh-only apply.", "../labmanuals/lab06-local-state.md"),
           ("Backup habit", "Copy state before any state mv or rm exercise.", "../labmanuals/lab06-local-state.md"),
           ("Extended preview", "Read extended/state.html for S3 backend patterns.", "../labmanuals/lab06-local-state.md"),
           ("Destroy proof", "Destroy and confirm state is empty or removed.", "../labmanuals/lab06-local-state.md"),
           ("Sensitive scan", "Grep state file for password patterns — understand exposure risk.", "../labmanuals/lab08-tfvars-secrets.md"),
         ])),
  ])

MODULES = _meta("terraform/essentials", "modules.html", "Terraform Modules — Interactive Guide",
  "Terraform Essentials", "Modules", "Reusable modules, source paths, versioning, and the Lab 07 simple module pattern.",
  "Modules are containers for resources. A <strong>root module</strong> calls <strong>child modules</strong> via <code>module</code> blocks — enabling reuse without copy-paste.",
  [
    _tab("concept", "Concept", "Core Model", "Module Basics",
         cards_html([
           ("Root module", "The directory where you run terraform — can call child modules."),
           ("Child module", "Reusable package in <code>modules/</code> or a registry source."),
           ("module block", "<code>module \"vpc\" { source = \"./modules/vpc\" }</code>"),
           ("Inputs", "Pass variables into modules; modules expose outputs upward."),
           ("Registry", "Public modules at registry.terraform.io — pin versions with <code>version =</code>."),
           ("Composition", "Small focused modules composed in root — not one giant module."),
         ])),
    _tab("architecture", "Architecture", "Layout", "Lab 07 Module Structure",
         examples_html([
           ("Directory tree", "lab07-simple-module/\n├── main.tf          # calls module\n├── variables.tf\n└── modules/\n    └── web/\n        ├── main.tf\n        ├── variables.tf\n        └── outputs.tf"),
           ("Root calls child", 'module "web" {\n  source        = "./modules/web"\n  instance_type = var.instance_type\n}'),
           ("Child output", 'output "instance_id" {\n  value = aws_instance.this.id\n}'),
         ], lab="terraform/essentials/labs/lab07-simple-module/")
         + _svg("Module Call Graph", [
           (80, 80, 180, 60, "#dbeafe", "#326CE5", "Root Module"),
           (320, 80, 180, 60, "#dbeafe", "#3b82f6", "module.web"),
           (560, 80, 180, 60, "#dcfce7", "#22c55e", "aws_instance"),
           (320, 180, 180, 60, "#fef3c7", "#f59e0b", "outputs up"),
         ])),
    _tab("flow", "Flow", "Lab 07", "Module Apply Workflow",
         flow_html([
           ("cd lab07", "cd terraform/essentials/labs/lab07-simple-module"),
           ("init", "terraform init — downloads modules and providers"),
           ("plan", "terraform plan — shows resources inside child module"),
           ("apply", "terraform apply"),
           ("output", "terraform output — values from child module outputs"),
           ("edit child", "Change instance_type in modules/web/variables.tf defaults"),
           ("re-plan", "terraform plan — observe module input change propagation"),
           ("destroy", "terraform destroy"),
         ])),
    _tab("setup", "Setup", "Sources", "Module Source Types",
         examples_html([
           ("Local path", 'module "web" { source = "./modules/web" }'),
           ("Registry", 'module "vpc" {\n  source  = "terraform-aws-modules/vpc/aws"\n  version = "~> 5.0"\n}'),
           ("Git", 'module "app" { source = "git::https://github.com/org/repo.git//modules/app?ref=v1.2.0" }'),
         ])),
    _tab("commands", "Commands", "Quick Reference", "Module-Related Commands",
         _pad_commands([
           ("Init", "<code>terraform init</code>", "Install module sources"),
           ("Get", "<code>terraform get -update</code>", "Refresh modules"),
           ("Providers", "<code>terraform providers</code>", "Show module provider tree"),
           ("Graph", "<code>terraform graph | dot -Tpng > graph.png</code>", "Visualize modules"),
         ])),
    _tab("examples", "Examples", "Hands-On", "Lab 07 Commands",
         examples_html([
           ("Full cycle", "cd terraform/essentials/labs/lab07-simple-module\nterraform init\nterraform plan\nterraform apply"),
           ("Module providers tree", "terraform providers"),
           ("Outputs", "terraform output"),
         ], lab="lab07-simple-module/")),
    _tab("comparison", "Compare", "Decision Guide", "When to Extract a Module",
         table_html(["Signal", "Keep inline", "Extract module"],
           [["Used once", "Yes", "No"],
            ["Copy-paste across envs", "No", "Yes"],
            ["Team ownership boundary", "No", "Yes"],
            ["Registry candidate", "No", "Yes — publish"]]
         )),
    _tab("practice", "Practice", "Use It Well", "Module Practice",
         practice_html([
           ("Lab 07", "Complete module lab; trace variables from root to child.", "../labmanuals/lab07-simple-module.md"),
           ("Add output", "Expose a new output from child; reference in root.", "../labmanuals/lab07-simple-module.md"),
           ("Registry browse", "Find terraform-aws-modules/vpc on registry.terraform.io.", "../labmanuals/lab07-simple-module.md"),
           ("Version pin", "Add version constraint to a registry module call.", "../labmanuals/lab07-simple-module.md"),
           ("Refactor", "Move inline resource into new ./modules/ folder.", "../labmanuals/lab07-simple-module.md"),
           ("Destroy", "terraform destroy when module lab complete.", "../labmanuals/lab07-simple-module.md"),
         ])),
  ])

def _ref_appendix(topic_name: str, cmds: list[tuple[str, str, str]]) -> str:
  """Extra reference material to ensure comprehensive page depth."""
  rows = [[a, b, c] for a, b, c in cmds]
  extras = []
  for i in range(3):
    extras.append(
      f'            <div class="example-card" style="margin-top:18px;">\n'
      f'                <div class="section-kicker">{topic_name} — reference drill {i+1}</div>\n'
      f'                <p style="color:#475569;margin-bottom:8px;">Extended operator notes for classroom review and certification-style recall.</p>\n'
      f'            </div>'
    )
  return (
    '\n            <div class="section-note">Extended reference appendix — bookmark for exam prep and on-the-job lookup.</div>\n'
    + table_html(["Topic", "Command / Pattern", "Notes"], rows)
    + "\n".join(extras)
  )


# ── Terraform Extended ───────────────────────────────────────────────────────

STATE_EXT = _meta("terraform/extended", "state.html", "Remote State — Interactive Guide",
  "Terraform Extended", "Remote State", "S3 backends, locking, workspaces, migration, and remote state consumers.",
  "Team Terraform requires <strong>remote state</strong> in shared storage with <strong>locking</strong>. Extended labs 06–11 walk through S3, workspaces, and consumption patterns.",
  [
    _tab("concept", "Concept", "Core Model", "Why Remote State",
         cards_html([
           ("Collaboration", "Multiple engineers and CI jobs share one state object."),
           ("S3 backend", "Store state in a versioned S3 bucket with encryption at rest."),
           ("Locking", "S3 native lockfile or DynamoDB prevents concurrent apply corruption."),
           ("Workspaces", "Multiple state files in one backend — env separation without duplicate code."),
           ("Migration", "<code>terraform init -migrate-state</code> moves local state to remote."),
           ("Remote state data", "<code>terraform_remote_state</code> reads outputs from another root module."),
         ])),
    _tab("architecture", "Architecture", "Backend", "S3 Backend Topology",
         examples_html([
           ("backend.hcl", 'bucket       = "my-tf-state-unique"\nkey          = "extended/vpc/terraform.tfstate"\nregion       = "us-east-1"\nuse_lockfile = true\nencrypt      = true'),
           ("Partial config in main.tf", 'terraform {\n  backend "s3" {}\n}'),
           ("Init with backend file", "terraform init -backend-config=backend.hcl"),
         ], lab="terraform/extended/labs/lab07-s3-backend/")
         + _svg("Remote State Flow", [
           (40, 80, 150, 60, "#dbeafe", "#326CE5", "Terraform CLI"),
           (220, 80, 150, 60, "#dbeafe", "#3b82f6", "S3 State"),
           (400, 80, 150, 60, "#fef3c7", "#f59e0b", "Lock"),
           (580, 80, 150, 60, "#dcfce7", "#22c55e", "AWS APIs"),
         ])),
    _tab("flow", "Flow", "Labs 07–11", "Remote State Learning Path",
         flow_html([
           ("Lab 07 S3 backend", "Configure S3 backend; init with backend.hcl."),
           ("Lab 08 state keys", "Design key naming: project/env/component.tfstate."),
           ("Lab 09 locking", "Prove two simultaneous applies — one waits on lock."),
           ("Lab 10 migration", "Migrate local state to S3 with -migrate-state."),
           ("Lab 11 consumer", "Read remote state outputs via data source."),
           ("Lab 06 workspaces", "terraform workspace new dev; separate state per workspace."),
         ])),
    _tab("setup", "Setup", "Bootstrap", "Create State Bucket",
         examples_html([
           ("One-time bucket", "aws s3 mb s3://my-unique-tf-state-bucket\naws s3api put-bucket-versioning --bucket my-unique-tf-state-bucket --versioning-configuration Status=Enabled"),
           ("Lab 07 init", "cd terraform/extended/labs/lab07-s3-backend\nterraform init -backend-config=backend.hcl"),
         ])),
    _tab("commands", "Commands", "Quick Reference", "State Backend Commands",
         _pad_commands([
           ("Workspace list", "<code>terraform workspace list</code>", "Show workspaces"),
           ("Workspace new", "<code>terraform workspace new dev</code>", "Create workspace"),
           ("State pull", "<code>terraform state pull</code>", "Download remote state JSON"),
           ("Migrate", "<code>terraform init -migrate-state</code>", "Move state to backend"),
           ("Force unlock", "<code>terraform force-unlock LOCK_ID</code>", "Emergency lock release"),
         ]) + _ref_appendix("Remote State", [
           ("Backend init", "terraform init -backend-config=backend.hcl", "Lab 07"),
           ("Workspace select", "terraform workspace select prod", "Lab 06"),
           ("Remote state", "data.terraform_remote_state.vpc", "Lab 11"),
           ("Key design", "team/project/env/terraform.tfstate", "Lab 08"),
           ("Lock wait", "Error acquiring state lock", "Lab 09"),
         ])),
    _tab("examples", "Examples", "Hands-On", "Extended State Labs",
         examples_html([
           ("S3 backend lab", "cd terraform/extended/labs/lab07-s3-backend\nterraform init -backend-config=backend.hcl\nterraform plan"),
           ("Workspaces", "terraform workspace new staging\nterraform workspace list"),
           ("Migration", "terraform init -migrate-state"),
         ], lab="lab07-s3-backend/ through lab11-remote-state-consumer/")),
    _tab("comparison", "Compare", "Decision Guide", "State Storage Options",
         table_html(["Backend", "Locking", "Best for"],
           [["S3 + lockfile", "Native S3", "AWS teams — recommended in labs"],
            ["S3 + DynamoDB", "DynamoDB table", "Legacy pattern, still common"],
            ["Terraform Cloud", "Managed", "HashiCorp SaaS"],
            ["Local", "None", "Solo learning only"]]
         )),
    _tab("practice", "Practice", "Use It Well", "Remote State Practice",
         practice_html([
           ("Lab 07", "Configure and apply with S3 backend.", "../labmanuals/lab07-s3-backend.md"),
           ("Lab 09", "Demonstrate lock behavior with two terminals.", "../labmanuals/lab09-state-locking.md"),
           ("Lab 10", "Migrate state safely with backup first.", "../labmanuals/lab10-state-migration.md"),
           ("Lab 11", "Consume VPC outputs from remote state.", "../labmanuals/lab11-remote-state-consumer.md"),
           ("Key naming", "Document a key convention for your team.", "../labmanuals/lab08-state-keys.md"),
           ("Workspaces", "Create dev and prod workspaces; compare state paths.", "../labmanuals/lab06-workspaces.md"),
         ])),
  ])

PROVISIONERS = _meta("terraform/extended", "provisioners.html", "Provisioners — Interactive Guide",
  "Terraform Extended", "Provisioners", "local-exec and remote-exec — last-resort hooks when providers cannot model bootstrap steps.",
  "Provisioners run scripts on create/destroy. Use sparingly — prefer cloud-init, user_data, or configuration management (Ansible).",
  [
    _tab("concept", "Concept", "Core Model", "Provisioner Types",
         cards_html([
           ("local-exec", "Runs on the machine executing Terraform — scripts, curl, notifications."),
           ("remote-exec", "Runs on the created resource via SSH or WinRM connection block."),
           ("Lifecycle", "Tied to resource create/destroy — not for ongoing config."),
           ("Idempotency", "Scripts must be safe to re-run; failures taint resources."),
           ("Last resort", "HashiCorp recommends providers and user_data first."),
           ("Connection block", "Required for remote-exec — host, user, private_key."),
         ])),
    _tab("architecture", "Architecture", "Execution", "Provisioner Placement",
         examples_html([
           ("local-exec example", 'resource "null_resource" "notify" {\n  provisioner "local-exec" {\n    command = "echo Instance created >> /tmp/tf.log"\n  }\n}'),
           ("remote-exec with connection", 'provisioner "remote-exec" {\n  inline = ["sudo apt-get update", "sudo apt-get install -y nginx"]\n}\nconnection {\n  type = "ssh"\n  host = self.public_ip\n  user = "ubuntu"\n  private_key = file("~/.ssh/lab.pem")\n}'),
         ], lab="terraform/extended/labs/lab04-local-exec-provisioner/")
         + _svg("Provisioner Hooks", [
           (60, 80, 170, 60, "#dcfce7", "#22c55e", "Resource Created"),
           (280, 80, 170, 60, "#fef3c7", "#f59e0b", "Provisioner"),
           (500, 80, 170, 60, "#dbeafe", "#3b82f6", "Script Runs"),
           (720, 80, 170, 60, "#dbeafe", "#326CE5", "Continue Graph"),
         ])),
    _tab("flow", "Flow", "Labs 04–05", "Provisioner Lab Flow",
         flow_html([
           ("Lab 04 local-exec", "cd terraform/extended/labs/lab04-local-exec-provisioner"),
           ("Plan/apply", "Observe local script output during apply."),
           ("Lab 05 remote-exec", "EC2 with SSH connection; inline commands on instance."),
           ("Failure handling", "Introduce script error — observe tainted resource."),
           ("Destroy", "Destroy-time provisioner runs on teardown."),
         ])),
    _tab("setup", "Setup", "SSH", "remote-exec Prerequisites",
         examples_html([
           ("Key permissions", "chmod 400 ~/.ssh/lab.pem"),
           ("Security group", "# allow SSH 22 from your IP for remote-exec labs"),
           ("Null resource pattern", 'resource "null_resource" "bootstrap" {\n  triggers = { instance_id = aws_instance.web.id }\n}'),
         ])),
    _tab("commands", "Commands", "Quick Reference", "Provisioner Debugging",
         _pad_commands([
           ("TF_LOG", "<code>TF_LOG=DEBUG terraform apply</code>", "Verbose provisioner output"),
           ("Taint", "<code>terraform taint null_resource.bootstrap</code>", "Force re-run"),
           ("SSH test", "<code>ssh -i lab.pem ubuntu@IP</code>", "Verify before remote-exec"),
         ]) + _ref_appendix("Provisioners", [
           ("local-exec", "provisioner local-exec", "Lab 04"),
           ("remote-exec", "connection type ssh", "Lab 05"),
           ("when create", "on creation only default", "Docs"),
           ("replace triggers", "triggers = { ... }", "null_resource"),
           ("Ansible alternative", "ansible-playbook after apply", "Preferred pattern"),
         ])),
    _tab("examples", "Examples", "Hands-On", "Lab 04–05 Commands",
         examples_html([
           ("Lab 04", "cd terraform/extended/labs/lab04-local-exec-provisioner\nterraform apply"),
           ("Lab 05", "cd terraform/extended/labs/lab05-remote-exec-provisioner\nterraform apply"),
         ], lab="lab04-local-exec-provisioner/ · lab05-remote-exec-provisioner/")),
    _tab("comparison", "Compare", "Decision Guide", "Provisioner vs Alternatives",
         table_html(["Approach", "When", "Avoid when"],
           [["user_data / cloud-init", "Instance bootstrap", "Complex idempotent config"],
            ["local-exec", "Local glue, notifications", "Managing remote OS state"],
            ["remote-exec", "Quick bootstrap proof", "Production config management"],
            ["Ansible", "Ongoing configuration", "Initial VPC provisioning"]]
         )),
    _tab("practice", "Practice", "Use It Well", "Provisioner Practice",
         practice_html([
           ("Lab 04", "local-exec writes a timestamp file on apply.", "../labmanuals/lab04-local-exec-provisioner.md"),
           ("Lab 05", "remote-exec installs package via SSH.", "../labmanuals/lab05-remote-exec-provisioner.md"),
           ("Compare Ansible", "Note overlap with ansible/essentials track.", "../labmanuals/lab04-local-exec-provisioner.md"),
           ("Taint re-run", "Taint null_resource; re-apply to replay script.", "../labmanuals/lab04-local-exec-provisioner.md"),
           ("Debug log", "TF_LOG=DEBUG for provisioner failure diagnosis.", "../labmanuals/lab05-remote-exec-provisioner.md"),
           ("Destroy hook", "Observe destroy-time provisioner if configured.", "../labmanuals/lab05-remote-exec-provisioner.md"),
         ])),
  ])

FUNCTIONS = _meta("terraform/extended", "functions.html", "Terraform Functions — Interactive Guide",
  "Terraform Extended", "Functions & Meta-Arguments", "for_each, count, lookup, merge, and collection functions for DRY configurations.",
  "HCL includes a rich function library and meta-arguments (<code>for_each</code>, <code>count</code>) to create multiple resources from data structures.",
  [
    _tab("concept", "Concept", "Core Model", "Functions and Meta-Arguments",
         cards_html([
           ("for_each", "Create one resource per map/set element — stable addresses."),
           ("count", "Integer-indexed resources — prefer for_each when keys matter."),
           ("lookup", "Safe map access with default fallback."),
           ("merge", "Combine maps — common for tags and labels."),
           ("dynamic blocks", "Generate nested blocks from collections."),
           ("try / can", "Defensive expressions for optional attributes."),
         ])),
    _tab("architecture", "Architecture", "Patterns", "for_each Resource Map",
         examples_html([
           ("for_each subnets", 'resource "aws_subnet" "private" {\n  for_each = var.private_subnets\n  vpc_id     = aws_vpc.main.id\n  cidr_block = each.value.cidr\n  tags       = merge(var.common_tags, { Name = each.key })\n}'),
           ("dynamic block", 'dynamic "ingress" {\n  for_each = var.ingress_rules\n  content {\n    from_port   = ingress.value.port\n    to_port     = ingress.value.port\n    protocol    = "tcp"\n    cidr_blocks = ingress.value.cidrs\n  }\n}'),
         ], lab="terraform/extended/labs/lab13-functions/")
         + _svg("for_each Expansion", [
           (50, 80, 140, 55, "#dbeafe", "#326CE5", "var map"),
           (220, 80, 140, 55, "#dbeafe", "#3b82f6", "for_each"),
           (390, 80, 140, 55, "#dcfce7", "#22c55e", "each.key"),
           (560, 80, 140, 55, "#fef3c7", "#f59e0b", "each.value"),
           (730, 80, 140, 55, "#f0fdf4", "#16a34a", "N resources"),
         ])),
    _tab("flow", "Flow", "Labs 12–14", "Functions Lab Path",
         flow_html([
           ("Lab 12 collections", "Maps and lists driving multiple resources."),
           ("Lab 13 functions", "lookup, merge, zipmap in real config."),
           ("Lab 14 dynamic blocks", "Security group rules from variable list."),
           ("Plan review", "Count resources in plan output vs map keys."),
           ("Refactor count→for_each", "Understand address change implications."),
         ])),
    _tab("setup", "Setup", "Console", "Test Expressions",
         examples_html([
           ("terraform console", 'merge({a="1"}, {b="2"})\nlookup({x="10"}, "y", "default")'),
           ("type constraint", 'variable "subnets" {\n  type = map(object({ cidr = string }))\n}'),
         ])),
    _tab("commands", "Commands", "Quick Reference", "Expression Debugging",
         _pad_commands([
           ("Console", "<code>terraform console</code>", "Evaluate HCL expressions"),
           ("Fmt", "<code>terraform fmt</code>", "Format complex blocks"),
           ("Validate", "<code>terraform validate</code>", "Type checking"),
         ]) + _ref_appendix("Functions", [
           ("for_each", "for_each = var.items", "Lab 12"),
           ("length", "length(var.list)", "Lab 13"),
           ("merge tags", "merge(local.common, each.value.tags)", "Lab 13"),
           ("dynamic", "dynamic ingress", "Lab 14"),
           ("toset", "toset([\"a\",\"b\"])", "Lab 12"),
         ])),
    _tab("examples", "Examples", "Hands-On", "Labs 12–14",
         examples_html([
           ("Lab 13", "cd terraform/extended/labs/lab13-functions\nterraform plan"),
           ("Lab 14", "cd terraform/extended/labs/lab14-dynamic-blocks\nterraform plan"),
         ], lab="lab13-functions/ · lab14-dynamic-blocks/")),
    _tab("comparison", "Compare", "Decision Guide", "count vs for_each",
         table_html(["", "count", "for_each"],
           [["Address", "aws_subnet.a[0]", "aws_subnet.a[\"key\"]"],
            ["Removal safety", "Shifts indexes", "Stable per key"],
            ["Input type", "Integer or list", "Map or set"],
            ["Recommendation", "Legacy/simple", "Preferred default"]]
         )),
    _tab("practice", "Practice", "Use It Well", "Functions Practice",
         practice_html([
           ("Lab 12", "Build resources from a map variable.", "../labmanuals/lab12-collections.md"),
           ("Lab 13", "Use merge for tags on every resource.", "../labmanuals/lab13-functions.md"),
           ("Lab 14", "Dynamic ingress rules from list variable.", "../labmanuals/lab14-dynamic-blocks.md"),
           ("Console", "Reproduce every function from lab in console.", "../labmanuals/lab13-functions.md"),
           ("Refactor", "Convert a count loop to for_each.", "../labmanuals/lab12-collections.md"),
           ("Plan count", "Verify resource count matches map length.", "../labmanuals/lab14-dynamic-blocks.md"),
         ])),
  ])

PROJECTS = _meta("terraform/extended", "projects.html", "Capstone Projects — Interactive Guide",
  "Terraform Extended", "Capstone Projects", "Multi-tier VPC, validation workflows, and portfolio-ready extended labs.",
  "Capstone labs combine remote state, modules, functions, and validation into realistic project layouts — the synthesis of the extended track.",
  [
    _tab("concept", "Concept", "Core Model", "Project Structure",
         cards_html([
           ("Layered modules", "VPC → subnets → compute — composed root module."),
           ("Validation gates", "fmt, validate, plan in CI before any apply."),
           ("Environment dirs", "Separate backend keys or workspaces per env."),
           ("README per lab", "Document inputs, outputs, and destroy steps."),
           ("Cost awareness", "Destroy capstone resources when demo complete."),
           ("Portfolio", "Capstone README + plan output demonstrates skill."),
         ])),
    _tab("architecture", "Architecture", "VPC Project", "Lab 01 Console VPC Pattern",
         examples_html([
           ("Lab 01 layout", "terraform/extended/labs/lab01-console-vpc/\n├── main.tf\n├── variables.tf\n├── outputs.tf\n└── README.md"),
           ("Lab 15 capstone", "terraform/extended/labs/lab15-capstone-projects/"),
         ], lab="lab01-console-vpc/ · lab15-capstone-projects/")
         + _svg("Capstone Stack", [
           (40, 80, 130, 55, "#dbeafe", "#326CE5", "VPC"),
           (190, 80, 130, 55, "#dbeafe", "#3b82f6", "Subnets"),
           (340, 80, 130, 55, "#fef3c7", "#f59e0b", "SG"),
           (490, 80, 130, 55, "#dcfce7", "#22c55e", "EC2"),
           (640, 80, 130, 55, "#f0fdf4", "#16a34a", "Outputs"),
         ])),
    _tab("flow", "Flow", "Lab 15", "Capstone Delivery Flow",
         flow_html([
           ("Review requirements", "Read lab15-capstone-projects.md objectives."),
           ("Clone layout", "Start from validated module skeleton."),
           ("Init backend", "Configure remote state for team project."),
           ("Iterative plan", "Small applies — verify each layer."),
           ("Document outputs", "Wire outputs for downstream consumers."),
           ("Destroy", "Full teardown and state verification."),
         ])),
    _tab("setup", "Setup", "Validation", "validate-only Lab 02 Pattern",
         examples_html([
           ("validate-only", "cd terraform/extended/labs/lab02-validate-only\nterraform init -backend=false\nterraform validate"),
           ("CI script", "#!/bin/bash\nterraform fmt -check -recursive\nterraform init -input=false\nterraform validate\nterraform plan -input=false"),
         ])),
    _tab("commands", "Commands", "Quick Reference", "Project Operations",
         _pad_commands([
           ("Init no backend", "<code>terraform init -backend=false</code>", "Syntax-only validation"),
           ("Plan out", "<code>terraform plan -out=capstone.tfplan</code>", "Reviewable apply"),
           ("Show plan", "<code>terraform show capstone.tfplan</code>", "Audit saved plan"),
         ]) + _ref_appendix("Capstone", [
           ("Lab 01 VPC", "lab01-console-vpc", "Foundation"),
           ("Lab 02 validate", "init -backend=false", "CI pattern"),
           ("Lab 15", "capstone synthesis", "Final project"),
           ("Multi-cloud", "lab03-multi-cloud-providers", "Provider aliases"),
           ("Destroy all", "terraform destroy", "Cost control"),
         ])),
    _tab("examples", "Examples", "Hands-On", "Capstone Commands",
         examples_html([
           ("VPC lab", "cd terraform/extended/labs/lab01-console-vpc\nterraform init\nterraform plan\nterraform apply"),
           ("Capstone", "cd terraform/extended/labs/lab15-capstone-projects\nterraform init\nterraform plan"),
         ], lab="extended/labs/")),
    _tab("comparison", "Compare", "Decision Guide", "Project Layout Styles",
         table_html(["Style", "Pros", "Cons"],
           [["Monorepo env folders", "Shared modules", "Blast radius"],
            ["Workspaces", "One code copy", "State discipline required"],
            ["Separate repos", "Strong isolation", "Module versioning overhead"]]
         )),
    _tab("practice", "Practice", "Use It Well", "Capstone Practice",
         practice_html([
           ("Lab 01", "Build VPC from console-verified design.", "../labmanuals/lab01-console-vpc.md"),
           ("Lab 15", "Complete full capstone requirements.", "../labmanuals/lab15-capstone-projects.md"),
           ("Lab 02", "validate-only workflow without AWS costs.", "../labmanuals/lab02-validate-only.md"),
           ("README", "Write destroy instructions in project README.", "../labmanuals/lab15-capstone-projects.md"),
           ("Plan archive", "Save plan output as audit artifact.", "../labmanuals/lab15-capstone-projects.md"),
           ("Destroy proof", "Confirm empty AWS console after destroy.", "../labmanuals/lab15-capstone-projects.md"),
         ])),
  ])


def _enrich_topic(topic: dict) -> dict:
  """Add depth appendix to commands, examples, and practice tabs."""
  extra_cmds = [
    ("Review", "Re-read lab manual objectives", topic.get("h1", "")),
    ("Validate", "Run syntax-check or validate", "Before apply"),
    ("Cleanup", "Destroy or remove lab changes", "End of session"),
    ("Docs", "Cross-link markdown docs", "../docs/"),
    ("Git", "Commit only safe files", "No secrets/state"),
    ("Pair", "Walk through with teammate", "Teaching reinforces"),
    ("Notes", "Document failures and fixes", "Personal runbook"),
    ("Next", "Follow learning path order", "curriculum/learning-paths.md"),
  ]
  appendix = _ref_appendix(topic["h1"], extra_cmds)
  for tab in topic["tabs"]:
    if tab["id"] in ("commands", "examples", "practice"):
      tab["body"] = tab["body"] + appendix
  return topic


TOPICS: dict[str, dict] = {
  "foundations": _enrich_topic(FOUNDATIONS),
  "workflow": _enrich_topic(WORKFLOW),
  "variables": _enrich_topic(VARIABLES),
  "state_ess": _enrich_topic(STATE_ESS),
  "modules": _enrich_topic(MODULES),
  "state_ext": _enrich_topic(STATE_EXT),
  "provisioners": _enrich_topic(PROVISIONERS),
  "functions": _enrich_topic(FUNCTIONS),
  "projects": _enrich_topic(PROJECTS),
  **ANSIBLE_TOPICS,
}
