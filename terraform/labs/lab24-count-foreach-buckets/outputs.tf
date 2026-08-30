output "count_bucket_names" {
  description = "Buckets made by count, in index order. [*] is the splat operator, valid only on count instances."
  value       = aws_s3_bucket.by_count[*].bucket
}

output "each_bucket_names" {
  description = "Buckets made by for_each, keyed by name. A for expression keeps this readable at any instance count."
  value       = { for key, bucket in aws_s3_bucket.by_each : key => bucket.bucket }
}

output "each_bucket_versioning" {
  description = "Versioning status per for_each instance, read back from the resource rather than the variable."
  value       = { for key, cfg in aws_s3_bucket_versioning.by_each : key => cfg.versioning_configuration[0].status }
}

output "each_bucket_tags" {
  description = "Tags per for_each instance, proving each instance is configured differently."
  value       = { for key, bucket in aws_s3_bucket.by_each : key => bucket.tags }
}
