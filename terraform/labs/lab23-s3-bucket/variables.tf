variable "aws_region" {
  description = "AWS region the bucket is created in."
  type        = string
  default     = "us-east-2"
}

variable "bucket_prefix" {
  description = "Leading part of the bucket name; two random words are appended to make it globally unique."
  type        = string
  default     = "tf-lab23"
}

variable "versioning_status" {
  description = "Bucket versioning state: Enabled or Suspended."
  type        = string
  default     = "Enabled"
}

variable "force_destroy" {
  description = "Allow terraform destroy to delete the bucket even when it still contains objects."
  type        = bool
  default     = true
}

variable "object_key" {
  description = "Key (path) of the demonstration object uploaded into the bucket."
  type        = string
  default     = "hello.txt"
}
