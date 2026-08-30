# Multiple Providers in One Configuration

Backs lab 13. Covers registering more than one provider in a single root module, how Terraform
decides which provider handles which resource, and provider aliases — the same provider configured
two different ways.

## Two providers, one root module

A configuration can register as many providers as it needs. Lab13 uses two:

```hcl
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws    = { source = "hashicorp/aws", version = "~> 5.0" }
    random = { source = "hashicorp/random", version = "~> 3.0" }
  }
}

provider "aws" { region = var.aws_region }
provider "random" {}

resource "random_pet" "label" { length = 2 }

output "provider_composition" {
  value = { aws_region = var.aws_region, generated_label = random_pet.label.id }
}
```

Terraform routes each resource to a provider by the prefix of its type: `aws_*` goes to the `aws`
provider, `random_*` to `random`. There is no configuration needed to connect them, and no ordering
problem — the dependency graph spans providers freely, so an `aws_instance` can take its name from a
`random_pet` and Terraform will resolve the order. Lab23 and lab24 both rely on that: an
`aws_s3_bucket` name built from a `random_pet` or a `random_id`.

`provider "random" {}` is empty because the random provider has nothing to configure. It could be
omitted entirely; declaring it in `required_providers` is sufficient.

**Visual summary:** [`../html/concepts.html`](../html/concepts.html)

## Aliases for the same provider twice

The more common real case is one provider configured two ways — usually two regions:

```hcl
provider "aws" {
  region = "us-east-2"
}

provider "aws" {
  alias  = "east1"
  region = "us-east-1"
}

resource "aws_s3_bucket" "primary" {
  bucket = "${var.project}-primary"
}

resource "aws_s3_bucket" "replica" {
  provider = aws.east1
  bucket   = "${var.project}-replica"
}
```

Resources with no `provider` argument use the unaliased default. To pass an aliased provider into a
child module, use `providers` (plural) on the `module` block:

```hcl
module "dr_network" {
  source = "./modules/network"

  providers = {
    aws = aws.east1
  }
}
```

Note the asymmetry: `provider` (singular) on a resource, `providers` (plural, a map) on a module.

Everything in this track outside these examples uses a single unaliased `us-east-2` provider.

## Command reference

```bash
cd terraform/labs/lab13-multi-provider
terraform init
terraform plan
terraform apply
terraform providers        # confirm both providers resolved
terraform destroy
```

## Where next

- Provisioners, the next Advanced topic: [`11-provisioners.md`](11-provisioners.md)
- Where the state for a multi-provider stack lives: [`13-remote-state.md`](13-remote-state.md)
- How several root modules are laid out in one repository:
  [`17-project-structure.md`](17-project-structure.md)

## Hands-On Labs

| Lab | Description |
|---|---|
| [Lab 13: Multi-provider configuration](../labmanuals/lab13-multi-provider.md) | Two providers in one root module, and provider aliases |
