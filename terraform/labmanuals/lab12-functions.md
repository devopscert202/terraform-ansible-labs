# Lab 12 — Functions

| | |
|---|---|
| **Goal** | Transform values with Terraform's built-in functions inside a `locals` block, and use `terraform console` to test an expression before committing it to a file. |
| **Time** | 40–50 minutes |
| **Tier** | Intermediate |
| **Files** | `terraform/labs/lab12-functions/` |

## Overview

A **function** takes values in and returns a new value: `lower("ABC")` returns `"abc"`. Terraform
ships a fixed set of them and you cannot write your own, so learning the catalogue is the whole
skill. They group into families — string, collection, numeric, network, encoding, and a few
defensive ones — and you reach for them whenever a value needs reshaping between the input a human
types and the format AWS demands.

Functions cannot be called at the top level of a file. They live inside expressions, and the usual
home for a non-trivial expression is a `locals` block, which you met in Lab 06. The other tool this
lab introduces is `terraform console`, an interactive prompt where you evaluate an expression and
see the answer immediately instead of guessing and re-running `plan`. You will work through one
family per step at that prompt, then see the same functions used for real in the configuration.

This lab creates no resources, so it is free and needs no AWS credentials.

## What you will build

| Resource | Purpose | Cost |
|---|---|---|
| `local.slug` | `lower()` and `replace()` turn a display name into a safe identifier | Free |
| `local.unique_cidrs` | `toset()`, `tolist()`, `sort()` deduplicate and order a list | Free |
| `local.cidr_count` | `length()` counts the result | Free |
| `local.subnet_prefix` | `cidrsubnet()` carves a subnet range out of a larger one | Free |
| `local.config_json` | `jsonencode()` renders an object as a JSON string | Free |
| `local.summary` | `format()` builds a display string | Free |

## Before you start

- [ ] Lab 11 completed ([lab11-collections.md](lab11-collections.md))
- [ ] You know what a list, a set, and a map are
- [ ] Working directory: `../labs/lab12-functions/` (no AWS credentials needed)

## Steps

### Step 1 — Read the locals block

```bash
cd terraform/labs/lab12-functions
cat main.tf
```

Every value is built by a function, and several nest one call inside another. Read nested calls
from the inside out: in `lower(replace(var.application, " ", "-"))` the `replace()` runs first and
its result becomes the argument to `lower()`.

### Step 2 — Open the console

```bash
terraform init
terraform console
```

**Expected output**

```text
>
```

The prompt is `>`. It evaluates one expression at a time and prints the result. Nothing you type here
changes any file or any infrastructure. Stay at this prompt for Steps 3 through 12.

### Step 3 — String functions: reshape text

```text
lower("Payments API")
replace("payments api", " ", "-")
```

**Expected output**

```text
"payments api"
"payments-api"
```

`lower()` folds the case. `replace()` swaps every occurrence of its second argument for the third.
Chained, they turn a human-written name into an identifier safe to use in a resource name — which
is exactly what `local.slug` does.

### Step 4 — String functions: uppercase and join

```text
upper("prod")
join(", ", ["web", "api", "db"])
```

**Expected output**

```text
"PROD"
"web, api, db"
```

`join()` collapses a list into one string with a separator between elements. It is the function you
want whenever a provider argument takes a comma-separated string but your data is a list.

### Step 5 — Collection functions: remove duplicates

```text
toset(["10.0.2.0/24","10.0.1.0/24","10.0.1.0/24"])
```

**Expected output**

```text
toset([
  "10.0.1.0/24",
  "10.0.2.0/24",
])
```

`toset()` converts a list to a set, and sets cannot hold duplicates, so the repeated CIDR is gone.
Three values in, two out. The `toset([...])` wrapper in the display is Terraform telling you the
result's type, not part of the value.

### Step 6 — Collection functions: get a stable order

```text
sort(tolist(toset(["10.0.2.0/24","10.0.1.0/24","10.0.1.0/24"])))
```

**Expected output**

```text
tolist([
  "10.0.1.0/24",
  "10.0.2.0/24",
])
```

A set has no defined order, so you cannot rely on how it prints. `tolist()` converts back to a list
and `sort()` puts it in a predictable order. This three-function chain is the standard idiom for
cleaning up a list of CIDRs, and it is what `local.unique_cidrs` uses.

### Step 7 — Numeric functions: count and compare

```text
length(["a","b","c"])
max(3, 9, 1)
min(3, 9, 1)
```

**Expected output**

```text
3
9
1
```

`length()` works on lists, sets, maps, and strings, which makes it the function you use to turn a
collection into the number that `count` requires — you did exactly that in Lab 10.

### Step 8 — Network functions: carve out a subnet range

```text
cidrsubnet("10.20.0.0/16", 8, 12)
```

**Expected output**

```text
"10.20.12.0/24"
```

`cidrsubnet(prefix, newbits, netnum)` splits a range. Adding `8` bits to a `/16` gives `/24`
blocks, and `12` selects the thirteenth of them, counting from zero. Doing this arithmetic by hand
is a reliable source of outages, so let the function do it.

### Step 9 — Network functions: pick a specific host address

```text
cidrhost("10.20.12.0/24", 5)
```

**Expected output**

```text
"10.20.12.5"
```

`cidrhost()` returns one address from inside a range. Use it when something needs a fixed IP that
must still move correctly if the surrounding CIDR changes.

### Step 10 — Encoding functions: produce JSON

```text
jsonencode({name = "payments-api", ports = [80, 443]})
```

**Expected output**

```text
"{\"name\":\"payments-api\",\"ports\":[80,443]}"
```

`jsonencode()` turns a Terraform object into a JSON *string*. The backslashes are escaped quotes,
because the result is a single string containing JSON, not an object. IAM policy documents and
user-data payloads both want this form.

### Step 11 — Formatting functions: build a display string

```text
format("%s uses %d CIDRs", "payments-api", 2)
```

**Expected output**

```text
"payments-api uses 2 CIDRs"
```

`format()` substitutes values into a template: `%s` for a string, `%d` for a number. Terraform has
no `printf`; this is it.

### Step 12 — Defensive functions: supply a fallback

```text
coalesce(null, "", "fallback")
try(tonumber("abc"), 0)
```

**Expected output**

```text
"fallback"
0
```

`coalesce()` returns its first argument that is neither null nor empty. `try()` evaluates its
arguments in order and returns the first that does not error — here `tonumber("abc")` fails, so the
fallback `0` is returned. These keep a configuration working when an optional input is absent.

### Step 13 — Evaluate this configuration's own values

```text
local.slug
local.unique_cidrs
local.summary
```

**Expected output**

```text
"payments-api"
tolist([
  "10.0.1.0/24",
  "10.0.2.0/24",
])
"payments-api uses 2 unique CIDR(s)"
```

The console loads the configuration in the current directory, so `var.*`, `local.*`, and — after an
apply — resource attributes are all available. You are now reading the same values you traced by
hand in Steps 3 through 11.

### Step 14 — Leave the console

```text
exit
```

You are back at your shell prompt. If an expression is wrong the console prints the error and stays
open, which makes it far cheaper than discovering the same mistake during an `apply`.

### Step 15 — Apply and read every result at once

```bash
terraform apply -auto-approve
```

**Expected output**

```text
Apply complete! Resources: 0 added, 0 changed, 0 destroyed.

Outputs:

cidr_count = 2
config_json = "{\"cidrs\":[\"10.0.1.0/24\",\"10.0.2.0/24\"],\"name\":\"payments-api\"}"
slug = "payments-api"
subnet_prefix = "10.20.12.0/24"
summary = "payments-api uses 2 unique CIDR(s)"
unique_cidrs = tolist([
  "10.0.1.0/24",
  "10.0.2.0/24",
])
```

`0 added` is correct — there are no resources, only computed outputs.

### Step 16 — Change an input and watch every derived value follow

```bash
terraform apply -auto-approve -var 'application=Billing Service'
```

**Expected output**

```text
config_json = "{\"cidrs\":[\"10.0.1.0/24\",\"10.0.2.0/24\"],\"name\":\"billing-service\"}"
slug = "billing-service"
summary = "billing-service uses 2 unique CIDR(s)"
```

One input changed and three outputs updated, because each is derived rather than typed out. That is
the reason to push transformation into functions instead of hand-writing both forms.

## Done when

- [ ] `terraform console` opens and you evaluated an expression from every family above
- [ ] You produced `"payments-api"` with `lower()` and `replace()`
- [ ] `toset()` reduced three CIDRs to two, and `sort(tolist(...))` ordered them
- [ ] `cidrsubnet("10.20.0.0/16", 8, 12)` returned `"10.20.12.0/24"`
- [ ] `apply` prints all six outputs with `0 added`
- [ ] Overriding `application` changed `slug`, `summary`, and `config_json` together

## If something fails

| Symptom | Likely cause | Fix |
|---|---|---|
| `Call to unknown function` | Misspelled name, or a function from another language | Terraform has no `printf`; use `format()` |
| `Invalid function argument` | Wrong type passed in | `sort()` needs a list; wrap a set in `tolist()` |
| `Invalid index` on `cidrsubnet` | `netnum` too large for the given `newbits` | `newbits = 8` allows `netnum` `0`–`255` |
| `Invalid value for "v" parameter` on `cidrhost` | Host number outside the range | Keep it below the range's host count |
| Console shows `(known after apply)` | Value depends on a resource not yet created | Run `apply` first, then reopen the console |
| Console will not exit | Waiting on an unclosed bracket or quote | Close it, or press `Ctrl-C` then type `exit` |
| `Variables not allowed` | Function or `var.` used at the top level of a file | Move the expression inside a `locals` block |

## Cleanup

```bash
terraform destroy -auto-approve
```

## Next steps

- Deep dive: [docs/09-collections-functions.md](../docs/09-collections-functions.md)
- Visual: [Concept page — this lab's topic](../html/concepts.html#lab12-functions)
- Continue to [Lab 13 — Multi-provider configuration](lab13-multi-provider.md)
