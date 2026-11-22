from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
DATASET = REPO_ROOT / "evals" / "datasets" / "eval_v0.json"


@pytest.fixture
def dataset_path() -> Path:
    return DATASET
