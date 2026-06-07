resource "aws_s3_bucket" "exports" { bucket = "tenant-export-bucket" }
resource "aws_iam_role" "worker" { name = "worker-role" }
