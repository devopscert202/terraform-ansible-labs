# Project Layout and Environment Promotion

Backs no single lab — it is the reference for assembling everything the track teaches into one
repository. Covers how to organise a repository once one directory is no longer enough, and how
environments get promoted from dev to production. The capstone build itself is walked through
resource by resource in [`08-capstone.md`](08-capstone.md), at lab10.

## From one directory to a repository

Every lab so far has been one root module in one directory. Real projects outgrow that, and the
question becomes where to draw the boundaries.

The unit that matters is the **state file**, because state is the unit of locking, of applying, and
of blast radius. Everything in one state is planned together, applied together, and can be
destroyed together. So "how should I split my repository" is really "what should share a state
file".

Three shapes, in increasing order of separation:

| Shape | Layout | Splits state by |
|---|---|---|
| Single root | One directory, all resources | Nothing. One state for everything |
| Root per environment | `environments/dev/`, `environments/prod/`, calling shared `modules/` | Environment |
| Root per environment per component | `environments/prod/network/`, `environments/prod/app/` | Environment and component |

```
terraform/
├── modules/                 <- reusable, no backend, no provider block
│   ├── network/
│   └── app/
└── environments/
    ├── dev/
    │   ├── network/         <- root module: backend + provider + module calls
    │   │   ├── main.tf
    │   │   └── backend.hcl
    │   └── app/
    └── prod/
        ├── network/
        └── app/
```

Two rules make this work, and both come from earlier labs. Modules never declare a `backend` or a
`provider` — those belong to the root, so the same module can serve dev and prod (lab09). And each
root gets its own state key, so each has its own lock and its own blast radius (lab18).

The trade-off is real: more roots means more applies to run and more coordination between them,
usually via `terraform_remote_state` (lab20). Start with fewer roots and split when a specific pain
appears — a slow plan, a lock you keep waiting on, a change that keeps touching things it should
not.

**Visual summary:** [`../html/concepts.html`](../html/concepts.html)

Multiple providers and provider aliases, which a dev/prod split often needs, are
[`10-multi-provider.md`](10-multi-provider.md) at lab13.

## Environment promotion

The same code should reach production, having been proven everywhere else first. What changes
between environments is inputs, not code.

| Stage | State | Approval | Applied by |
|---|---|---|---|
| **Dev** | `labs/dev/...` | None. Destroy and rebuild freely | Anyone on the team |
| **Staging** | `labs/staging/...` | Plan reviewed on the pull request | CI, on merge |
| **Prod** | `labs/prod/...` | Plan reviewed and explicitly approved | CI only, never a laptop |

Three practices make this work in practice:

- **Pin module and provider versions in prod.** Unpinned means someone else's commit changes your
  production infrastructure with no action from you.
- **Apply the saved plan.** `terraform plan -out=tfplan` in one stage, `terraform apply tfplan` in
  the next, so the diff that gets approved is the diff that runs. Treat the plan file as secret; it
  contains the full diff, secrets included.
- **Detect drift on a schedule.** A nightly `terraform plan` that reports non-empty output tells you
  someone changed production by hand, near when it happened rather than months later.

## Project hygiene checklist

- [ ] Remote backend with `encrypt = true` and `use_lockfile = true`
- [ ] S3 bucket versioning enabled, with a lifecycle policy on old versions
- [ ] State key includes both environment and component
- [ ] No credentials in version control — environment variables locally, OIDC in CI
- [ ] `terraform.tfvars.example` documents every variable, with placeholders
- [ ] `.gitignore` covers `.terraform/`, `*.tfstate`, `*.tfstate.backup`, `backend.hcl`, real `*.tfvars`
- [ ] `.terraform.lock.hcl` **is** committed
- [ ] Provider and module versions pinned
- [ ] `terraform fmt -check -recursive` and `terraform validate` run in CI
- [ ] README states how to `init` with the right backend config
- [ ] Every AWS resource tagged for ownership and cost
- [ ] Teardown documented, and actually run on lab and sandbox accounts

## Where next

- Where state for these layouts lives, including state keys per environment and component:
  [`13-remote-state.md`](13-remote-state.md)
- Why workspaces are not the environment boundary this document describes:
  [`12-workspaces.md`](12-workspaces.md)
- Writing the child modules these roots call: [`07-modules.md`](07-modules.md)
- The capstone build, resource by resource: [`08-capstone.md`](08-capstone.md)

## Labs this reference draws on

| Lab | What it contributes |
|---|---|
| [Lab 09: Modules](../labmanuals/lab09-modules.md) | The child module that several roots reuse |
| [Lab 13: Multi-provider configuration](../labmanuals/lab13-multi-provider.md) | More than one provider per root module |
| [Lab 18: State keys and locking](../labmanuals/lab18-state-keys-locking.md) | One state key per environment and component |
| [Lab 20: Remote state consumer](../labmanuals/lab20-remote-state-consumer.md) | How one root reads another's outputs |
