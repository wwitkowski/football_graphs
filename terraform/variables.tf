variable "minio_user" {
  description = "MinIO Root User"
  type        = string
}

variable "minio_password" {
  description = "MinIO Root Password"
  type        = string
  sensitive   = true
}