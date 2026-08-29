# Terraform Core Workflow

Deep dive for lab04. Covers what each command in the loop actually guarantees, how to read plan
output symbol by symbol, when a saved plan matters, and when you must re-run `init`.

## The loop

```
init  ──>  validate  ──>  plan  ──>  apply  ──>  ...  ──>  destroy
 │                          │          │                     │
 once per                 as often   when the              when you
 directory, and           as you     plan is               are finished
 after certain changes    like       what you wanted
```

The shape of this loop is **propose, then commit** — the same idea as opening a pull request
before merging. `plan` proposes and changes nothing; `apply` commits. Every command except `apply`
and `destroy` is safe to run at any time, on anything, as often as you like.

Treat `plan` as mandatory, not optional. It is the only step between a typo and a deleted
database, and it costs a few seconds.

**Visual summary:** [`../../html/basic.html`](../../html/basic.html)

## What each command is for

| Command | Reads | Writes | Calls the cloud API? |
|---|---|---|---|
| `terraform init` | `.tf` files, lock file | `.terraform/`, `.terraform.lock.hcl` | Registry only, not your account |
| `terraform fmt` | `.tf` files | `.tf` files (rewrites them) | No |
| `terraform validate` | `.tf` files, provider schemas | Nothing | No |
| `terraform plan` | `.tf` files, state, live infrastructure | Nothing (unless `-out`) | Yes — read-only |
| `terraform apply` | `.tf` files, state, live infrastructure | Your cloud account, state | Yes — read and write |
| `terraform destroy` | State | Your cloud account, state | Yes — deletes |
| `terraform output` | State | Nothing | No |

Two things in that table surprise people. `validate` makes no API calls at all, so it cannot tell
you whether your credentials work or whether an instance type is available in your region — it
only checks that your configuration is internally coherent. And `plan` *does* call the API, in
read-only mode, which is why it can detect that someone deleted a resource behind your back.

## Lab04: the full cycle at zero cost

Lab04's entire configuration is one resource and one output:

```hcl
resource "random_string" "example" {
  length  = 12
  special = false
  upper   = false
}

output "generated_value" {
  value = random_string.example.result
}
```

`random_string` comes from the `hashicorp/random` provider. It creates nothing in any cloud, needs
no credentials, and costs nothing — but Terraform manages it exactly like an EC2 instance. It has
an address, it goes in state, it appears in plans, and `destroy` removes it. That makes it the
right place to learn the mechanics of the loop, because you can create and destroy it thirty times
in a row with no consequences.

## Reading a plan

The plan is the most important output Terraform produces, and it repays learning to read
carefully. Every proposed change is prefixed with a symbol:

| Symbol | Action | What it means |
|---|---|---|
| `+` | create | A new object will be created |
| `-` | destroy | An existing object will be deleted |
| `~` | update in place | An attribute changes without recreating the object |
| `-/+` | replace | Destroy then create. **The object's ID changes.** |
| `+/-` | replace, create first | Same, but the new one is created before the old is destroyed (`create_before_destroy`) |
| `<=` | read | A data source will be read during apply |

Then a summary line:

```text
Plan: 1 to add, 0 to change, 0 to destroy.
```

Read that line every single time. On an AWS lab, a number in the "destroy" column you were not
expecting is your cue to stop.

`-/+` deserves particular suspicion. It means Terraform cannot change the attribute you edited on
a live object, so it will delete and rebuild — losing anything not stored elsewhere. Terraform
labels the responsible attribute `# forces replacement`, so you can always find out which one
triggered it.

Values not yet knowable appear as `(known after apply)`. That is normal for anything the provider
assigns, such as an ID or a public IP.

## Apply

```bash
terraform apply
```

`apply` re-plans, shows you the diff, and asks for confirmation. You must type `yes` — not `y`,
not Enter. This is on purpose.

`-auto-approve` skips the prompt. It is right for CI, where a human already reviewed the plan, and
wrong on your laptop, where the prompt is the last thing standing between you and an accident.

When apply finishes:

```text
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.

Outputs:

generated_value = "x7kq2mzp4nrt"
```

State is now written. `terraform.tfstate` records that `random_string.example` exists and what its
attributes are. Run `plan` again immediately and you should see
`No changes. Your infrastructure matches the configuration.` — that is idempotency, working.

## Saved plans

By default `apply` computes a fresh plan. You can instead capture one and apply exactly it:

```bash
terraform plan -out=tfplan
terraform show tfplan      # human-readable render of the saved file
terraform apply tfplan     # applies precisely this, no new plan, no prompt
```

This closes a real gap. Without a saved plan, the diff a reviewer approved and the diff `apply`
executes are two separate computations — infrastructure or variables could have changed in
between. With one, they are the same artifact. That is why CI pipelines plan in one stage, publish
the file, and apply it in the next.

The saved plan file contains the full resource diff, including any sensitive values. Treat it as a
secret: never commit it, and expire it from CI artifact storage.

## Destroy

```bash
terraform destroy
```

`destroy` deletes everything in the current directory's state, walking the dependency graph
backwards so dependents go before their dependencies. It shows a plan and prompts, just like
`apply`.

Two habits worth forming now. Run `destroy` at the end of every AWS lab — an instance left running
bills by the hour whether you use it or not. And remember that `destroy` only knows about
resources in *this* directory's state; anything you created by hand in the console is invisible to
it and must be cleaned up by hand.

## When you must re-run `init`

`init` is not once-per-lifetime. Run it again after any of these:

| Trigger | Why |
|---|---|
| Added or changed a `required_providers` entry | A new plugin must be downloaded |
| Added, changed, or removed a `backend` block | Where state lives has changed (lab17) |
| Added a new `module` block or changed a module `source` | Module code must be fetched (lab09) |
| Freshly cloned the repository | `.terraform/` is gitignored, so no plugins are present |

The symptom of a missing `init` is an error telling you to run `terraform init`. Terraform is
generally explicit about this, so take it at face value.

## Useful flags

| Flag | Effect | Use with care? |
|---|---|---|
| `-out=FILE` | Save the plan to a file | No, always safe |
| `-var 'name=value'` | Set one variable for this run | No |
| `-var-file=FILE` | Load variables from a file | No |
| `-destroy` | Plan a teardown without executing it | No — this is how you preview `destroy` |
| `-refresh=false` | Skip refreshing state from the API. Faster, but the plan may be based on stale facts | Yes |
| `-target=ADDRESS` | Restrict the operation to one resource and its dependencies | **Yes.** Debugging only |

`-target` is the one to be wary of. It applies part of your configuration, which leaves state
partially converged and hides errors in whatever you excluded. HashiCorp's own documentation
describes it as an escape hatch for exceptional situations. Never build a routine or a pipeline
around it.

## Command reference

```bash
cd terraform/labs/lab04-plan-apply-destroy
terraform init
terraform plan
terraform apply
terraform output                 # all outputs
terraform show                   # everything in state, human-readable
terraform plan                   # again: expect "No changes"
terraform destroy
```

## Where next

- The quality gates that belong in front of every `apply`: [`05-quality.md`](05-quality.md)
- What state is doing under all of this: [`../intermediate/07-state.md`](../intermediate/07-state.md)

## Hands-On Labs

| Lab | Description |
|---|---|
| [Lab 04: Plan, Apply, Destroy](../../labmanuals/lab04-plan-apply-destroy.md) | The full create-and-teardown cycle with outputs, at no cost |
