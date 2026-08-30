# Terraform Quality: Format, Validate, and Review

Backs lab 05. Covers the three checks that belong in front of every `apply`, their exact exit codes,
and precisely how far a `sensitive` output is hidden — which is less far than most people assume.

## Three checks, three different questions

Terraform gives you three cheap gates before anything reaches your account. They answer different
questions and none of them substitutes for another.

| Check | Question | Contacts the cloud? | Catches |
|---|---|---|---|
| `terraform fmt` | Is it written in the canonical style? | No | Indentation, alignment, spacing |
| `terraform validate` | Is it internally coherent? | No | Unknown arguments, wrong types, broken references, missing required arguments |
| `terraform plan` | What would it actually do? | Yes, read-only | Drift, permission errors, invalid values the API rejects, unavailable instance types |

The useful analogy is language: **fmt** is handwriting, **validate** is grammar, **plan** is
meaning. A sentence can be beautifully written and grammatical and still be false. A green
`validate` does not predict a green `plan`, because `validate` never asks AWS anything.

**Visual summary:** [`../html/concepts.html`](../html/concepts.html)

## terraform fmt

`fmt` rewrites `.tf`, `.tfvars`, and `.tftest.hcl` files into HashiCorp's canonical style. There
are no options to configure — that is the feature. Nobody argues about brace placement in review
because there is exactly one correct answer and a command that produces it.

```bash
terraform fmt              # rewrite files in this directory
terraform fmt -recursive   # include subdirectories, e.g. modules/
terraform fmt -check       # report only, change nothing
terraform fmt -diff        # show what would change, as a unified diff
```

`fmt` only touches whitespace and alignment. It will never reorder your arguments, rename
anything, or alter a value. Running it cannot break a working configuration.

### The exit codes

This is the detail that matters for automation, and it is easy to get wrong:

| Situation | Printed | Exit code |
|---|---|---|
| Every file already canonical | nothing | `0` |
| One or more files need formatting | the offending filenames | **`3`** |
| Genuine error, e.g. unparseable file | an error message | `1` |

`fmt -check` exits **3**, not 1, when files need formatting. Both are non-zero, so a plain
`if terraform fmt -check` test in a shell script or CI job behaves correctly either way — but if
you ever branch on the specific code, `3` is the number to test for. `1` means something actually
went wrong, such as a file too malformed to parse.

Lab05 has you break the formatting deliberately, watch `fmt -check` exit `3` and name the file,
run `fmt`, and confirm it then exits `0`.

## terraform validate

```bash
terraform validate
```

`validate` checks your configuration against the provider schemas: does `aws_instance` really have
an argument by that name, is that string where a number belongs, does
`aws_security_group.web.id` refer to a block that exists.

It requires `init` first, because the schemas live in the downloaded provider plugins. If you have
not run `init`, `validate` tells you so rather than guessing.

For a validation-only CI job on a repository with a remote backend, skip backend initialisation
entirely:

```bash
terraform init -backend=false
terraform validate
```

That needs no cloud credentials and no state access, which makes it safe to run on a pull request
from a fork.

What `validate` cannot see:

- Whether your credentials work
- Whether `t3.nano` is offered in `us-east-2`
- Whether the AMI your data source filters for exists
- Whether you have quota, or permission
- Whether the plan would destroy production

All five of those are `plan`'s job.

### Errors you will actually hit

| Message | Cause | Fix |
|---|---|---|
| `Missing required provider` | `init` was skipped | `terraform init` |
| `Reference to undeclared resource` | Typo in an address, or the block was renamed | Match the `resource` block's type and name exactly |
| `Unsupported argument` | Argument does not exist on that resource, or you are on an older provider | Check the registry docs for your provider version |
| `Invalid value for variable` | The value violates the `type` or a `validation` block | Align the value with the `variable` declaration |
| `Missing required argument` | A mandatory argument is absent | Add it |

## Sensitive outputs, precisely

Lab05 marks one output sensitive:

```hcl
output "formatted_example" {
  description = "Random string, hidden from normal CLI display."
  value       = random_string.formatted_example.result
  sensitive   = true
}
```

Now the part almost everyone gets wrong. `sensitive = true` hides the value in **some** displays
and not others. Here is the complete picture:

| Command | Shows the value? |
|---|---|
| `terraform apply` summary | No — prints `<sensitive>` |
| `terraform plan` diff | No — prints `(sensitive value)` |
| `terraform output` (no arguments) | No — prints `<sensitive>` |
| `terraform output formatted_example` | **Yes, in full** |
| `terraform output -raw formatted_example` | **Yes, in full**, without the surrounding quotes |
| `terraform output -json` | **Yes, in full** |
| `terraform.tfstate` on disk | **Yes, in plain text** |

Two conclusions follow, and both matter.

**You do not need `-raw` to reveal a sensitive output.** Naming the output prints it in full.
`-raw` does one narrow thing: it strips the quotes and JSON escaping so the value can be piped
into another command. That is a formatting flag, not an access flag.

**Redaction is not a security boundary.** It is a guard against accidental disclosure — a secret
scrolling past in a shared screen share, or landing in a CI log that a hundred people can read.
It stops the accident. It does not stop anyone who wants the value, because anyone who can run
`terraform output` can name it, and anyone who can read the state file already has it.

The real control is protecting the state file, which is discussed in
[`06-state.md`](06-state.md).

Marking an output sensitive has one further consequence worth knowing: Terraform propagates the
mark. If you build another value from a sensitive one, that value becomes sensitive too, and
Terraform refuses to render it in places it cannot redact. `nonsensitive()` deliberately removes
the mark, and lab07 uses it to publish the *length* of a password without publishing the password.

## A review checklist

Before you approve any apply:

- [ ] `terraform fmt -check -recursive` exits `0`
- [ ] `terraform validate` exits `0`
- [ ] The plan summary line was read, and the destroy count is what you expected
- [ ] Every `# forces replacement` in the plan is understood and acceptable
- [ ] No credentials or secrets appear in any file being committed
- [ ] Tags and names follow whatever convention the account uses

## In a CI pipeline

The conventional four stages, cheapest first, so the fast checks fail fast:

```bash
terraform init -backend=false   # no state, no credentials needed
terraform fmt -check -recursive # exits 3 if anything is unformatted
terraform validate              # exits 1 on a schema or reference error
terraform plan -out=tfplan      # needs credentials and backend access
```

Only the last stage needs real access, and read-only credentials are enough for it. If the
pipeline then applies, it should apply the saved `tfplan` file rather than re-planning, so the diff
that gets executed is the diff that got reviewed. Treat that file as sensitive — it contains the
full resource diff, secret values included.

An editor integration closes the loop nicely: the official Terraform extension for VS Code
formats on save using the same rules as the CLI, so `fmt -check` never fails in CI because it
never had anything to find.

## Command reference

```bash
cd terraform/labs/lab05-fmt-validate
terraform init
terraform fmt -check          # exits 3 while the file is unformatted
terraform fmt                 # rewrite it
terraform fmt -check          # now exits 0
terraform validate
terraform apply
terraform output                        # sensitive output shows as <sensitive>
terraform output formatted_example      # named: prints in full
terraform destroy
```

## Where next

- Variables, and how `sensitive` behaves on inputs as well as outputs:
  [`05-variables.md`](05-variables.md)
- Why the state file is the thing actually worth protecting:
  [`06-state.md`](06-state.md)

## Hands-On Labs

| Lab | Description |
|---|---|
| [Lab 05: Format and Validate](../labmanuals/lab05-fmt-validate.md) | `fmt` exit codes, `validate` errors, and exactly how far a sensitive output is hidden |
