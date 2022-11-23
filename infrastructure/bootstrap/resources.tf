resource "aws_s3_bucket" "artifacts" {
  bucket = var.artifacts_bucket_name
  acl    = "private"

  tags = {
    Name = var.artifacts_bucket_name
  }
}
