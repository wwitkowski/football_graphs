variable "minio_server" {
  description = "MinIO server endpoint"
  type        = string
}

variable "minio_user" {
  description = "MinIO root user"
  type        = string
}

variable "minio_password" {
  description = "MinIO root password"
  type        = string
  sensitive   = true
}

variable "python_user_secret_file" {
  description = "Path to save python user secret"
  type        = string
}

variable "spark_user_secret_file" {
  description = "Path to save spark user secret"
  type        = string
}