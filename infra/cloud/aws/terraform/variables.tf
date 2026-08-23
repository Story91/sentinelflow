variable "aws_region" {
  type        = string
  description = "AWS region for the learning deployment."
  default     = "eu-central-1"
}

variable "artifact_bucket" {
  type        = string
  description = "Globally unique private S3 bucket name."
}

