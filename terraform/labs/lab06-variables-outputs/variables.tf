# ---------------------------------------------------------------------------
# Primitive types: string, number, bool
# ---------------------------------------------------------------------------

variable "aws_region" {
  type        = string
  description = "AWS region the instance is created in."
  default     = "us-east-2"
}

variable "server_name" {
  type        = string
  description = "Value used for the Name tag on the EC2 instance."
  default     = "lab06-web"
}

variable "instance_type" {
  type        = string
  description = "EC2 instance size. Must be a t3 size to keep this lab cheap."
  default     = "t3.micro"
  nullable    = false

  validation {
    condition     = startswith(var.instance_type, "t3.")
    error_message = "instance_type must be a t3 size, for example t3.micro."
  }
}

variable "root_volume_gb" {
  type        = number
  description = "Root disk size in gibibytes. A number, so arithmetic works on it."
  default     = 8
}

variable "enable_detailed_monitoring" {
  type        = bool
  description = "Whether to turn on per-minute CloudWatch metrics. Bools accept only true or false."
  default     = false
}

# ---------------------------------------------------------------------------
# Collection types: list, set, map. Same element type, different behaviour.
# ---------------------------------------------------------------------------

variable "role_list" {
  type        = list(string)
  description = "A list: ordered, duplicates kept, addressed by position. Note the repeated web."
  default     = ["web", "api", "web"]
}

variable "role_set" {
  type        = set(string)
  description = "A set: unordered, duplicates discarded. Same default as role_list, different result."
  default     = ["web", "api", "web"]
}

variable "tags" {
  type        = map(string)
  description = "A map: values addressed by string key. Merged into every resource tag set."
  default = {
    Environment = "training"
    Owner       = "platform-team"
  }
}

# ---------------------------------------------------------------------------
# Structural types: object and tuple. Mixed attribute types, unlike collections.
# ---------------------------------------------------------------------------

variable "server_profile" {
  type = object({
    name       = string
    cpu_count  = number
    public     = bool
    department = optional(string, "unassigned")
    extra_tags = optional(map(string), {})
  })
  description = "One object with named attributes of different types. optional() attributes may be omitted."
  default = {
    name      = "lab06-web"
    cpu_count = 2
    public    = true
  }
}

variable "release_marker" {
  type        = tuple([string, number, bool])
  description = "A tuple: fixed length, each position has its own type. Here name, build number, is-stable."
  default     = ["al2023", 3, true]
}

# ---------------------------------------------------------------------------
# Nested types: the shapes real configurations use.
# ---------------------------------------------------------------------------

variable "disks" {
  type = list(object({
    device  = string
    size_gb = number
  }))
  description = "A list of objects. Order matters and entries need no unique name."
  default = [
    { device = "/dev/sdb", size_gb = 10 },
    { device = "/dev/sdc", size_gb = 20 },
  ]

  validation {
    condition     = min(var.disks[*].size_gb...) >= 8
    error_message = "Every disk needs size_gb of at least 8."
  }
}

variable "environments" {
  type = map(object({
    instance_type = string
    replicas      = number
  }))
  description = "A map of objects. Each entry is addressed by its key rather than its position."
  default = {
    dev  = { instance_type = "t3.micro", replicas = 1 }
    prod = { instance_type = "t3.small", replicas = 3 }
  }
}

# ---------------------------------------------------------------------------
# any, null, and sensitive
# ---------------------------------------------------------------------------

variable "freeform" {
  type        = any
  description = "Accepts any shape. Terraform cannot check it, so prefer a real type wherever you can."
  default     = { note = "any switches type checking off", count = 1 }
}

variable "owner_email" {
  type        = string
  description = "Optional contact address. Defaults to null, meaning deliberately absent."
  default     = null
}

variable "api_token" {
  type        = string
  description = "Placeholder credential, redacted in all Terraform output. Lab 07 covers supplying real secrets."
  default     = "lab06-placeholder-not-a-real-token"
  sensitive   = true
}

# ---------------------------------------------------------------------------
# Network inputs. The instance launches into the subnet these describe, so the
# lab never depends on the account holding a default VPC.
# ---------------------------------------------------------------------------

variable "vpc_cidr" {
  type        = string
  description = "Address range of the VPC this lab creates. Also the only source allowed to reach port 22."
  default     = "10.0.0.0/16"
}

variable "subnet_cidr" {
  type        = string
  description = "Address range of the subnet the instance launches into. Must sit inside vpc_cidr."
  default     = "10.0.1.0/24"
}

variable "subnet_az" {
  type        = string
  description = "Availability zone the subnet is created in. Must belong to aws_region."
  default     = "us-east-2a"
}
