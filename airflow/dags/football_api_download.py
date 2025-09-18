import os

import pendulum
from docker.types import Mount
from airflow.models import DAG, Variable
from airflow.providers.docker.operators.docker import DockerOperator

default_args = {
    "owner": "airflow",
    "depends_on_past": True,
    "retries": 0,
}

dag_id = os.path.basename(__file__).replace(".py", "")

REPO_OWNER = Variable.get("REPO_OWNER")
BACKEND_TAG = Variable.get("BACKEND_TAG", default_var="latest")
API_KEY = Variable.get("API_FOOTBALL_KEY")
DB_USER = Variable.get("FOOTGRAPH_DB_USER")
DB_PASSWORD = Variable.get("FOOTGRAPH_DB_PASSWORD")
DB_NAME = Variable.get("FOOTGRAPH_DB")
PROJECT_DATA = Variable.get("PROJECT_DATA")

with DAG(
    dag_id,
    default_args=default_args,
    schedule=None,
    start_date=pendulum.datetime(2025, 7, 18),
    catchup=True,
) as dag:
    run_docker_task = DockerOperator(
        task_id="download_ongoing",
        image=f"ghcr.io/{REPO_OWNER}/data_backend:{BACKEND_TAG}",
        api_version="auto",
        auto_remove="force",
        command="uv run python -m scripts.football_api.download_ongoing {{ ds }}",
        docker_url="unix://var/run/docker.sock",
        network_mode="project-net",
        mounts=[
            Mount(
                source=f"{PROJECT_DATA}/Secret/python_user",
                target="/root/.aws/credentials",
                type="bind",
                read_only=True
            )
        ],
        environment={
            "POSTGRES_HOST": "postgres",
            "FOOTGRAPH_DB_USER": DB_USER,
            "FOOTGRAPH_DB_PASSWORD": DB_PASSWORD,
            "FOOTGRAPH_DB": DB_NAME,
            "API_FOOTBALL_KEY": API_KEY
        }
    )

    run_docker_task
