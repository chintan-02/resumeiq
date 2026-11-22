from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
DATASET = REPO_ROOT / "evals" / "datasets" / "eval_v0.json"


@pytest.fixture
def dataset_path() -> Path:
    return DATASET


@pytest.fixture(autouse=True)
def _fresh_rate_limits():
    """Every test starts with empty rate-limit windows (all tests share one client address)."""
    from resumeiq_api.app import LIMITER

    LIMITER.reset()
    yield
    LIMITER.reset()
