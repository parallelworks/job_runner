import pathlib

import pytest
import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW_V4_PATH = ROOT / "v4.0.yaml"
WORKFLOW_V5_PATH = ROOT / "v5.0.yaml"


# v4.0 fixtures
@pytest.fixture(scope="session")
def workflow_text():
    return WORKFLOW_V4_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def workflow_data(workflow_text):
    return yaml.safe_load(workflow_text)


# v5.0 fixtures
@pytest.fixture(scope="session")
def v5_workflow_text():
    return WORKFLOW_V5_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def v5_workflow_data(v5_workflow_text):
    return yaml.safe_load(v5_workflow_text)
