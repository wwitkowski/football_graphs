output "python_user_secret" {
  value     = minio_iam_user.python_user.secret
  sensitive = true
}

output "spark_user_secret" {
  value     = minio_iam_user.spark_user.secret
  sensitive = true
}