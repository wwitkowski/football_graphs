module "minio" {
  source                  = "./minio"
  minio_server            = "localhost:9000"
  minio_user              = var.minio_user
  minio_password          = var.minio_password
  python_user_secret_file = "/home/rpi_user/Projects/football_graphs/Secret/python_user"
  spark_user_secret_file  = "/home/rpi_user/Projects/football_graphs/Secret/spark_user"
}