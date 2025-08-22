output "python_user_secret" {
  value     = module.minio.python_user_secret
  sensitive = true
}

output "spark_user_secret" {
  value     = module.minio.spark_user_secret
  sensitive = true
}