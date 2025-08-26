import os

from airflow.models.dag import DAG
from airflow.providers.docker.operators.docker import DockerOperator
import pendulum

default_args = {
    "owner": "airflow",
    "depends_on_past": True,
    "retries": 1,
}

dag_id = os.path.basename(__file__).replace(".py", "")


with DAG(
    dag_id,
    default_args=default_args,
    schedule=None,
    start_date=pendulum.datetime(2025, 7, 18),
    catchup=True,
) as dag:
    run_docker_task = DockerOperator(
        task_id="download",
        image="python:3.9",
        api_version="auto",
        auto_remove="force",
        command="uv run scripts/football_api/football_api.py --date {{ ds }}",
        docker_url="unix://var/run/docker.sock",
        network_mode="bridge",
    )

    run_docker_task
