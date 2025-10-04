import os

import pendulum
from airflow.hooks.base import BaseHook
from airflow.models import DAG, Variable
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

default_args = {
    "owner": "airflow",
    "depends_on_past": True,
    "retries": 0,
}

dag_id = os.path.basename(__file__).replace(".py", "")

REPO_OWNER = Variable.get("REPO_OWNER")
BACKEND_TAG = Variable.get("BACKEND_TAG", default_var="latest")
API_KEY = Variable.get("API_FOOTBALL_KEY")
PROJECT_DATA = Variable.get("PROJECT_DATA")

db_conn = BaseHook.get_connection('footgraph_db')

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
        network_mode="football_graphs_project-net",
        mounts=[
            Mount(
                source=f"{PROJECT_DATA}/Secret/python_user",
                target="/opt/airflow/.aws/credentials",
                type="bind",
                read_only=True
            )
        ],
        environment={
            "POSTGRES_HOST": db_conn.host,
            "POSTGRES_USER": db_conn.login,
            "POSTGRES_PASSWORD": db_conn.password,
            "POSTGRES_DB": db_conn.schema,
            "API_FOOTBALL_KEY": API_KEY
        },
        mount_tmp_dir=False,
    )

    run_docker_task
