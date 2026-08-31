# Workspaces

Backs lab 16. Covers what a workspace actually is, where its state file goes, `terraform.workspace`,
why HashiCorp advises against using workspaces as an environment boundary, and the one piece of
cross-lab bookkeeping lab16 carries.

## A workspace is a state file, and nothing else

Every lab directory before lab16 had exactly one state file, so applying the same configuration
twice with different values would overwrite the first result. A **workspace** is a named, separate
state file for the same configuration directory. Switch workspace and Terraform forgets the other
workspace's resources entirely — the code is shared, the state is not.

Every directory starts in a workspace called `default`, which is why the first fifteen labs never
had to mention the feature. Nothing you have done so far behaved differently because of it.

Be precise about the scope of what a workspace gives you, because the name suggests more:

| A workspace gives you | A workspace does **not** give you |
|---|---|
| A separate state file | A separate AWS account |
| Its name, readable from the configuration | Separate credentials |
| Independent create/destroy per workspace | An approval gate, or any visible indication of which one is active |
| One shared copy of the code | Any ability for one environment's code to differ from another's |

That list is the entire feature. Everything below follows from it.

**Visual summary:** [`../html/concepts.html`](../html/concepts.html)

## terraform.workspace

`terraform.workspace` is a built-in value holding the active workspace's name. It is not a variable:
you never declare it, it has no default, and nothing can override it. Lab16's whole configuration is
built around reading it:

```hcl
terraform { required_version = ">= 1.5.0" }

locals {
  environment = terraform.workspace
  labels      = { environment = terraform.workspace, managed_by = "terraform" }
}

resource "terraform_data" "workspace" { input = local.labels }
output "workspace" { value = terraform.workspace }
output "labels" { value = terraform_data.workspace.output }
```

Applied in `default`, the `labels` output reads `environment = "default"`. Applied in a workspace
called `dev`, the same code and the same command produce `environment = "dev"` — in a second,
independent resource, not a modification of the first. That is the isolation demonstrated.

The usual production use of `terraform.workspace` is naming: interpolating it into resource names and
tags so two workspaces do not collide on a globally unique name. Lab16 does that for real. Alongside
the `terraform_data` placeholder it creates one free `aws_vpc` per workspace, with the workspace name
in the `Name` tag and a CIDR selected by workspace name:

```hcl
locals {
  name     = "lab16-${terraform.workspace}"
  vpc_cidr = lookup(var.workspace_cidrs, terraform.workspace, "10.18.0.0/16")
}
```

Apply in both workspaces and there are **two VPCs live in the same account at once**, from one
configuration directory, at `10.16.0.0/16` and `10.17.0.0/16`. `terraform state list` in either
workspace shows exactly one `aws_vpc.env`, never two. That is the isolation claim tested against
AWS rather than asserted, and it is also the clearest statement of the limitation: both VPCs are in
the same account under the same credentials, because a workspace separates state and nothing else.

## The commands

```bash
terraform workspace show           # which one am I in
terraform workspace list           # * marks the active one
terraform workspace new dev        # create and switch, in one step
terraform workspace select dev     # switch to an existing one
terraform workspace delete dev     # only when it is not active and its state is empty
```

`workspace new` creates and switches at once, and Terraform says so plainly:

```text
Created and switched to workspace "dev"!

You're now on a new, empty workspace. Workspaces isolate their state,
so if you run "terraform plan" Terraform will not see any existing state
for this configuration.
```

Running `terraform state list` immediately afterwards is the proof, and it is worth doing once:

```text
No state file was found!
```

You applied a resource moments earlier and this workspace cannot see it.

## Where the state file goes

| Backend | `default` workspace | Workspace `dev` |
|---|---|---|
| Local (no `backend` block) | `./terraform.tfstate` | `./terraform.tfstate.d/dev/terraform.tfstate` |
| S3 | the `key` from `backend.hcl` | `env:/dev/<key>`, adjustable with `workspace_key_prefix` |

Lab16 uses local state, so after applying in both workspaces:

```text
./terraform.tfstate
./terraform.tfstate.d/dev/terraform.tfstate
```

Two files, two states, one directory of code.

## Why this is not an environment boundary

HashiCorp's own guidance is that workspaces are not the way to separate dev from production, and the
reasoning is worth stating bluntly rather than taking on authority.

| | Workspaces | Separate state keys |
|---|---|---|
| Configuration | One directory, one backend block | One directory per stack, or one backend file per environment |
| Switching | `terraform workspace select` | `terraform init -backend-config=<file>` |
| Credentials | **Shared. One set for all workspaces** | Separate per environment |
| Divergence between environments | Not possible — same code | Possible, and reviewable |
| Risk of applying to the wrong one | **High. The active workspace is invisible in your shell** | Low — you chose a directory |

Two failure modes do the damage.

**One backend configuration means one set of credentials.** Because the `backend` block is shared,
nothing technically prevents an apply in the `prod` workspace from running with dev credentials, or
the reverse. The boundary you want between environments — different accounts, different keys,
different permissions — is exactly the boundary a workspace cannot express.

**The active workspace is invisible.** Nothing in your shell prompt says `prod`. `terraform apply`
does not remind you, and the plan looks the same either way. The standard accident is applying a dev
change to production because you forgot to switch back, which is why lab16's troubleshooting advice
is to run `terraform workspace show` before every plan, and why the manual has a row for "plan shows
resources you thought you destroyed" — you are in a different workspace than you believe.

Where workspaces genuinely fit is ephemeral, identical environments: a per-branch sandbox, a
short-lived test stack, a feature preview that is created and thrown away. Same code, same
credentials, no approval gate needed, and no lasting consequence if you pick the wrong one.

For real environment boundaries, use separate state keys with separate credentials and separate
directories — labs 17 to 20, written up in [`13-remote-state.md`](13-remote-state.md). Make the
boundary something you have to walk through, not something you have to remember.

## The lab16 trap: cleanup is deferred

Lab16 is the only lab in the track you must **not** clean up when you finish it.
[Lab20](../labmanuals/lab20-remote-state-consumer.md) reads lab16's state files directly by path —
the `default` one and the `dev` one — as its producer:

```hcl
variable "upstream_state_path" {
  type        = string
  description = "Path to the producer lab's state file that this consumer reads."
  default     = "../lab16-workspaces/terraform.tfstate"
}
```

Destroy lab16 early and lab20 fails with `Failed to read state file`. Lab16's two VPCs are free, so
leaving them in place costs nothing — but they are real, and they count against the five-VPC limit in
`us-east-2`, so run lab20 promptly and then go back and destroy both workspaces.

Return after lab20 and tear down each workspace separately — destroying one leaves the other
untouched, and a workspace cannot be deleted while it is active or while its state still holds
resources:

```bash
terraform workspace select dev
terraform destroy -auto-approve
terraform workspace select default
terraform destroy -auto-approve
terraform workspace delete dev
```

## Command reference

```bash
cd terraform/labs/lab16-workspaces
terraform init
terraform workspace show                  # default
terraform apply -auto-approve
terraform workspace new dev
terraform state list                      # "No state file was found!" - the isolation, proven
terraform apply -auto-approve
terraform workspace list
find . -name '*.tfstate' -not -path './.terraform/*'
terraform workspace select default
terraform output                          # the default workspace's labels, still intact
# do NOT destroy yet - lab20 reads both of these state files
```

## Where next

- Real environment separation, with a key and credentials per environment:
  [`13-remote-state.md`](13-remote-state.md)
- The consumer that reads the two state files this lab leaves behind, at lab20:
  [`13-remote-state.md`](13-remote-state.md)
- Laying environments out as directories instead:
  [`17-project-structure.md`](17-project-structure.md)

## Hands-On Labs

| Lab | Description |
|---|---|
| [Lab 16: Workspaces](../labmanuals/lab16-workspaces.md) | `terraform workspace`, `terraform.workspace`, per-workspace state files, and why cleanup waits for lab20 |
