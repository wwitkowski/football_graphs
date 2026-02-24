import os

import pendulum
from airflow.models import DAG
from airflow.providers.docker.operators.docker import DockerOperator
from docker.types import Mount

default_args = {
    "owner": "airflow",
    "depends_on_past": True,
    "retries": 0,
}

dag_id = os.path.basename(__file__).replace(".py", "")
PROJECT_DATA_ROOT = os.environ.get("PROJECT_DATA", "")

with DAG(
    dag_id,
    default_args=default_args,
    schedule=None,
    start_date=pendulum.datetime(2025, 7, 18),
    catchup=True,
) as dag:
    run_docker_task = DockerOperator(
        task_id="download_ongoing",
        image="ghcr.io/{{ var.value.REPO_OWNER }}/data_backend:"
        "{{ var.value.BACKEND_TAG | default('latest', true) }}",
        api_version="auto",
        auto_remove="force",
        command=(
            "uv run python -m scripts.football_api.download_ongoing "
            "{{ ds }} {{ dag.dag_id }}"
        ),
        docker_url="unix://var/run/docker.sock",
        network_mode="football_graphs_project-net",
        mounts=[
            Mount(
                source=f"{PROJECT_DATA_ROOT}/Secret/python_user",
                target="/home/app/.aws/credentials",
                type="bind",
                read_only=True,
            )
        ],
        environment={
            "POSTGRES_HOST": "{{ conn.footgraph_db.host }}",
            "POSTGRES_USER": "{{ conn.footgraph_db.login }}",
            "POSTGRES_PASSWORD": "{{ conn.footgraph_db.password }}",
            "POSTGRES_DB": "{{ conn.footgraph_db.schema }}",
            "API_FOOTBALL_KEY": "{{ var.value.API_FOOTBALL_KEY }}",
        },
        mount_tmp_dir=False,
    )

    run_docker_task


