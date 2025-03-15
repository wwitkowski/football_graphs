terraform {
  required_providers {
    minio = {
      source = "aminueza/minio"
      version = "3.3.0"
    }
  }
}

provider "minio" {
  minio_server   = "localhost:9000"
  minio_user     = var.minio_user
  minio_password = var.minio_password
}

#############################
# Create Buckets
#############################
resource "minio_s3_bucket" "raw_data" {
  bucket = "raw-data"
  acl    = "private"
}

resource "minio_s3_bucket" "iceberg_data" {
  bucket = "iceberg-data"
  acl    = "private"
}

#############################
# Load External Policy Files
#############################

resource "minio_iam_policy" "raw_read_policy" {
  name   = "raw-read-policy"
  policy = file("${path.module}/policies/raw_read_policy.json")
}

resource "minio_iam_policy" "raw_write_policy" {
  name   = "raw-write-policy"
  policy = file("${path.module}/policies/raw_write_policy.json")
}

resource "minio_iam_policy" "iceberg_read_policy" {
  name   = "iceberg-read-policy"
  policy = file("${path.module}/policies/iceberg_read_policy.json")
}

resource "minio_iam_policy" "iceberg_write_policy" {
  name   = "iceberg-write-policy"
  policy = file("${path.module}/policies/iceberg_write_policy.json")
}

#############################
# Create IAM Users
#############################
resource "minio_iam_user" "python_user" {
  name = "python-user"
}

resource "minio_iam_user" "spark_user" {
  name = "spark-user"
}

#############################
# Attach Policies to Users
#############################
resource "minio_iam_user_policy_attachment" "raw_write_attachment" {
  user_name   = minio_iam_user.python_user.name
  policy_name = minio_iam_policy.raw_write_policy.name
}

resource "minio_iam_user_policy_attachment" "raw_read_attachment" {
  user_name   = minio_iam_user.spark_user.name
  policy_name = minio_iam_policy.raw_read_policy.name
}

resource "minio_iam_user_policy_attachment" "iceberg_read_attachment" {
  user_name   = minio_iam_user.spark_user.name
  policy_name = minio_iam_policy.iceberg_read_policy.name
}

resource "minio_iam_user_policy_attachment" "iceberg_write_attachment" {
  user_name   = minio_iam_user.spark_user.name
  policy_name = minio_iam_policy.iceberg_write_policy.name
}

#############################
# Outputs
#############################
output "python_user_secret" {
  value     = "${minio_iam_user.python_user.secret}"
  sensitive = true
}

output "spark_user_secret" {
  value     = "${minio_iam_user.spark_user.secret}"
  sensitive = true
}
