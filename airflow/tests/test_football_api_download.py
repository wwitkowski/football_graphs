from pathlib import Path
from unittest import mock

import pytest

from airflow.models.dagbag import DagBag
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.models.connection import Connection


MOCK_VARIABLES = {
    "REPO_OWNER": "my_repo_owner",
    "BACKEND_TAG": "latest",
    "API_FOOTBALL_KEY": "dummy_key",
    "PYTHON_USER_AWS_SECRET": "dummy_secret"
}

MOCK_CONNECTIONS = {
    "footgraph_db": Connection(conn_id="footgraph_db", conn_type="postgres", host="localhost", login="user", password="pass", schema="db")
}

@pytest.fixture(scope="module")
def dagbag():
    # Patch both Variable.get and BaseHook.get_connection before importing DAGs
    with mock.patch("airflow.models.variable.Variable.get") as mock_var_get, \
         mock.patch("airflow.hooks.base.BaseHook.get_connection") as mock_get_conn:
        
        mock_var_get.side_effect = lambda key, default_var=None: MOCK_VARIABLES.get(key, default_var)
        mock_get_conn.side_effect = lambda conn_id: MOCK_CONNECTIONS[conn_id]

        db = DagBag(dag_folder="airflow/dags", include_examples=False)
    yield db


def test_no_import_errors(dagbag):
    assert not dagbag.import_errors, f"DAG import errors: {dagbag.import_errors}"


def test_called_script_exists(dagbag):
    """Verify the script path in Docker command points to existing file"""

    for dag_id, dag in dagbag.dags.items():
        for task in dag.tasks:
            if not isinstance(task, DockerOperator):
                continue

            command_parts = task.command.split()
            if "-m" in command_parts:
                module_index = command_parts.index("-m") + 1
                module_name = command_parts[module_index]
                module_path = Path(module_name.replace(".", "/") + ".py")

                assert Path(module_path).exists(), (
                    f"Script called in {dag_id} dag not found: {module_path}"
                )
