import json
from pathlib import Path

import pytest

PLANS_DIR = Path(__file__).parent / "fixtures" / "plans"


@pytest.fixture()
def create_plan() -> dict:
    create_plan_path = PLANS_DIR / "nginx-create.json"
    return json.loads(create_plan_path.read_text())


@pytest.fixture()
def noop_plan() -> dict:
    noop_plan_path = PLANS_DIR / "nginx-noop.json"
    return json.loads(noop_plan_path.read_text())


@pytest.fixture()
def aws_sg_update_plan() -> dict:
    aws_plan_path = PLANS_DIR / "aws_sg_update.json"
    return json.loads(aws_plan_path.read_text())
