# Terraform State and Drift

Backs lab 08. Covers what state is for, what it contains — including secrets in plain text — how
refresh detects drift, and the inspection commands that mean you never have to open the file by
hand.

## Why state has to exist

Terraform's job is to make reality match your configuration. To do that it has to answer one
question that neither the configuration nor the cloud can answer alone:

> Is the thing described on line 12 of `main.tf` the same thing as instance `i-0a1b2c3d` in AWS?

Your configuration says "an instance named `web` should exist". AWS has an instance called
`i-0a1b2c3d`. Nothing connects the two. **State** is that connection: a JSON file mapping each
Terraform address to the real object's provider-assigned ID.

Remove state and Terraform loses its memory. It no longer knows `aws_instance.web` was ever
created, so the next `plan` proposes creating it — and you get a second instance, while the first
becomes an orphan nobody manages. This is why "just delete the state file" is never the fix.

**Visual summary:** [`../html/concepts.html`](../html/concepts.html)

## Where state lives

With no `backend` block, Terraform writes `terraform.tfstate` in the working directory. That is
the **local backend**, and it is the default. Lab08's configuration says so explicitly:

```hcl
# There is no backend block, so Terraform writes state to ./terraform.tfstate.
resource "random_pet" "server" {
  prefix = "lab08"
  length = 2
}

# A generated secret. It is stored in terraform.tfstate as plain text.
resource "random_password" "db" {
  length  = 16
  special = false
}

# A real VPC, so state holds an ID that AWS also holds.
resource "aws_vpc" "main" {
  cidr_block         = "10.8.0.0/16"
  enable_dns_support = true

  tags = {
    Lab  = "lab08"
    Name = random_pet.server.id
  }
}
```

That third resource is what makes the rest of this page matter. Two of the three resources are
generated locally, so losing their record costs nothing. The VPC is different: state is the only
copy on your machine of the `vpc-` ID AWS assigned. Delete the file and the VPC does not
disappear — it becomes an orphan that no configuration manages, and the next `apply` builds a second
one beside it.

Local state is correct for one person experimenting. It stops being adequate the moment a second
person or a CI job needs to apply the same configuration, because the file is on your laptop and
nobody else can see or lock it. Remote backends solve that, in lab17.

Every lab directory in this track has its own state file. That isolation is deliberate: an
experiment in lab08 cannot affect lab09, and you can destroy one without touching the other. It is
also why you always run Terraform from inside exactly one lab directory — Terraform reads the
`.tf` files in the current directory only.

## What state contains

| Content | Why it is there |
|---|---|
| Resource type, name, and provider-assigned ID | The core mapping, the reason state exists |
| Last known attribute values | So `plan` can diff without re-reading everything |
| Dependency information | So `destroy` can delete in the correct reverse order |
| Output values | So `terraform output` works without a plan |
| `serial` and `lineage` | Version counter and a unique ID for this state's history |
| **Secrets, in plain text** | Because attributes are recorded verbatim |

## State contains secrets in plain text

This is the single most important operational fact about state, and it is why lab08 generates a
`random_password` alongside the pet name.

`sensitive = true` on an output changes what the **CLI displays**. It has no effect whatsoever on
what is written to disk. Every attribute Terraform records goes into state as-is:

- Generated passwords (`random_password.db.result`)
- Values of sensitive input variables
- RDS master passwords, IAM secret access keys, private keys, TLS certificates
- Anything else the provider returns

Search lab08's state file after `apply` and you will find the password:

```bash
terraform apply
grep -o '"result": *"[^"]*"' terraform.tfstate
```

The consequences are non-negotiable:

- **Never commit a real state file.** `.gitignore` must cover `*.tfstate` and `*.tfstate.backup`.
  A state file in git history is a credential leak, and rewriting history does not un-leak it.
- **Treat a state file like the secret it contains.** Encrypt it at rest, restrict who can read
  it, and audit access. A remote backend on S3 with `encrypt = true` and a tight bucket policy is
  the standard answer (lab17).
- **Anyone who can read state can read your secrets.** Read access to the state bucket is
  effectively production credential access. Scope it accordingly.
- **Saved plan files have the same problem.** `terraform plan -out=tfplan` embeds the diff,
  secrets included.

## Refresh and drift

**Drift** is reality diverging from state — someone edited a resource in the console, a script
changed a tag, an instance was terminated by hand.

By default, `plan` and `apply` begin by **refreshing**: for every resource in state, Terraform asks
the provider what that object looks like right now. Then it computes the diff three ways:

```
   configuration  (what you want)
          │
          │  ◄── diff shown in the plan
          ▼
        state  ──refresh──►  reality (what actually exists)
```

Refresh reconciles state with reality. The plan then reconciles configuration with the refreshed
state. This is why `plan` needs API access even though it changes nothing, and why the plan can
surprise you with changes you did not write — it found drift.

| What happened outside Terraform | What the next plan proposes |
|---|---|
| A tag was added in the console | Remove it. Configuration is the source of truth |
| A tag Terraform manages was changed | Change it back, `~` update in place |
| The instance was terminated | Recreate it, `+` |
| An instance type was changed by hand | Change it back — possibly `-/+` replace |
| Nothing | `No changes.` |

Notice the pattern: Terraform reverts manual changes. It is not merging your console edit into the
configuration; it is restoring the state you declared. If you want to keep a console change, put it
in the `.tf` file.

`-refresh=false` skips the refresh. It makes `plan` faster on large configurations, at the cost of
planning against possibly stale facts. Reasonable in a tight development loop, a bad idea before
applying anything that matters.

## Inspecting state

Open the file once, out of curiosity, to see the JSON shape. Then use the commands, which are
safe, stable, and will not corrupt anything:

```bash
terraform state list                          # every managed address
terraform state show random_pet.server        # all recorded attributes of one resource
terraform show                                # everything, human-readable
terraform show -json | jq '.values.root_module.resources'
terraform output                              # just the outputs
```

```text
$ terraform state list
aws_vpc.main
random_password.db
random_pet.server
```

`terraform state list` output is exactly the set of addresses `destroy` would remove, which makes
it a good pre-teardown sanity check.

## Never hand-edit state

The file is JSON and it is tempting. Do not. It carries a `serial` counter and checksums, resources
reference each other, and a malformed edit produces failures far from the actual mistake.

Every legitimate state surgery has a command:

| Task | Command |
|---|---|
| Rename a resource in your configuration without recreating it | `terraform state mv OLD NEW` |
| Stop managing something, but leave it alive in the cloud | `terraform state rm ADDRESS` |
| Start managing something that already exists | `terraform import ADDRESS ID` (or an `import` block, Terraform 1.5+) |
| Force one resource to be recreated | `terraform apply -replace=ADDRESS` |
| Change which provider manages a resource | `terraform state replace-provider` |

Back up before any of them:

```bash
cp terraform.tfstate terraform.tfstate.$(date +%Y%m%d-%H%M%S).backup
```

Terraform also writes `terraform.tfstate.backup` automatically — the state as it was before the
most recent write. One generation only, so it saves you from the last mistake and no further.

### Replace, and the older `taint`

Sometimes a resource exists and matches its configuration, but is broken — a failed bootstrap
script, a corrupted volume. Configuration is correct, so `plan` proposes nothing. Force it:

```bash
terraform apply -replace=aws_instance.web
```

The older way was `terraform taint ADDRESS`, which marked the resource in state so the next apply
would replace it. It still works but is deprecated. Prefer `-replace`: it takes effect in the plan
you are about to review, rather than mutating state as a side effect and changing what a later
apply does.

## Command reference

```bash
cd terraform/labs/lab08-local-state
terraform init
terraform apply
ls -la terraform.tfstate                     # it exists now
terraform state list
terraform state show random_pet.server
terraform state show aws_vpc.main            # ~20 attributes, two of them yours
grep -o '"result": *"[^"]*"' terraform.tfstate   # the password, in plain text
terraform output                             # db_password shows as <sensitive>
terraform output db_password                 # named: prints in full
terraform plan                               # "No changes" — idempotent
terraform destroy

aws ec2 describe-vpcs --region us-east-2 \
  --filters 'Name=tag:Lab,Values=lab08' --query 'Vpcs[].VpcId'   # expect an empty list
```

## Where next

- Module addresses in state: [`07-modules.md`](07-modules.md)
- Moving state to S3 so a team can share it, with encryption and locking:
  [`13-remote-state.md`](13-remote-state.md)

## Hands-On Labs

| Lab | Description |
|---|---|
| [Lab 08: Local State](../labmanuals/lab08-local-state.md) | Create and inspect `terraform.tfstate`, match a real VPC ID against AWS, find a generated password in plain text, observe refresh |
