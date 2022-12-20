variable "aws_region" {
  type = string
}

variable "commit_sha" {
  type = string
}

variable "env_name" {
  type = string
}

variable "artifacts_bucket_name" {
  type = string
}

variable "lambda_archive_name" {
  type = string
}

variable "api_key_dangerous" {
  description = "Temporary location of the API key that needs to be used to something else"
  type        = string
}
