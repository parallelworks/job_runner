import pathlib

import pytest
import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW_PATH = ROOT / "v4.0.yaml"


@pytest.fixture(scope="session")
def workflow_text():
    return WORKFLOW_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def workflow_data(workflow_text):
    return yaml.safe_load(workflow_text)
