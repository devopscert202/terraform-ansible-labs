variable "application" {
  type        = string
  description = "Human-written application name, used to build a machine-safe slug."
  default     = "Payments API"
}

variable "cidrs" {
  type        = list(string)
  description = "Raw CIDR list, deliberately unsorted and containing a duplicate."
  default     = ["10.0.2.0/24", "10.0.1.0/24", "10.0.1.0/24"]
}
