from pathlib import Path

import pytest

from airflow.models.dagbag import DagBag
from airflow.providers.docker.operators.docker import DockerOperator


@pytest.fixture(scope="module")
def dagbag():
    return DagBag(dag_folder="airflow/dags", include_examples=False)


def test_no_import_errors(dagbag):
    assert not dagbag.import_errors, f"DAG import errors: {dagbag.import_errors}"


def test_called_script_exists(dagbag):
    """Verify the script path in Docker command points to existing file"""

    for dag_id, dag in dagbag.dags.items():
        for task in dag.tasks:
            if not isinstance(task, DockerOperator):
                continue

            command_parts = task.command.split()
            script_index = command_parts.index("run") + 1
            script = command_parts[script_index]

            assert Path(script).exists(), (
                f"Script called in {dag_id} dag not found: {script}"
            )
