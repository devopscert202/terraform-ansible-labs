variable "aws_region" {
  type        = string
  description = "Region the buckets are created in. us-east-2 has three availability zones: a, b and c."
  default     = "us-east-2"
}

variable "name_prefix" {
  type        = string
  description = "Prefix for every bucket name. A random suffix is appended to keep names globally unique."
  default     = "tf-lab24"
}

variable "bucket_names" {
  type        = list(string)
  description = "Ordered list driving the count example. Position in this list is the only identity a count instance has."
  default     = ["logs", "assets", "backups"]
}

variable "buckets" {
  type = map(object({
    versioning = bool
    tags       = map(string)
  }))
  description = "Map driving the for_each example. The key names the instance; the object configures it."
  default = {
    logs    = { versioning = true, tags = { Retention = "30d", Tier = "ops" } }
    assets  = { versioning = false, tags = { Retention = "none", Tier = "web" } }
    backups = { versioning = true, tags = { Retention = "1y", Tier = "data" } }
  }
}
