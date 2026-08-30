terraform {
  required_version = ">= 1.5.0"
}

# This lab creates no resources. Every value below is produced by a built-in
# function, so it is free to run and needs no credentials.
locals {
  # String functions: force lowercase, then swap spaces for hyphens.
  slug = lower(replace(var.application, " ", "-"))

  # Collection functions: toset() drops duplicates, sort() gives a stable order.
  unique_cidrs = sort(tolist(toset(var.cidrs)))

  # Numeric and network functions.
  cidr_count    = length(local.unique_cidrs)
  subnet_prefix = cidrsubnet("10.20.0.0/16", 8, 12)

  # Encoding functions: build a JSON string from a Terraform object.
  config_json = jsonencode({
    name  = local.slug
    cidrs = local.unique_cidrs
  })

  # Formatting: build a display string from several values.
  summary = format("%s uses %d unique CIDR(s)", local.slug, local.cidr_count)
}
