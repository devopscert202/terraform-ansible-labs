output "bucket_name" {
  description = "The globally unique name Terraform generated for the bucket."
  value       = aws_s3_bucket.lab.id
}

output "bucket_arn" {
  description = "ARN of the bucket."
  value       = aws_s3_bucket.lab.arn
}

output "bucket_region" {
  description = "Region the bucket was placed in."
  value       = aws_s3_bucket.lab.region
}

output "object_uri" {
  description = "s3:// URI of the uploaded object."
  value       = "s3://${aws_s3_bucket.lab.id}/${aws_s3_object.hello.key}"
}
