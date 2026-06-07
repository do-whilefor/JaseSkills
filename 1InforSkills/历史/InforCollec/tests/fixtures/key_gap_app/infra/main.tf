provider "aws" { region = "us-east-1" }
resource "aws_s3_bucket" "uploads" { bucket = "example-uploads" }
resource "aws_iam_role" "worker" { name = "worker-role" }
