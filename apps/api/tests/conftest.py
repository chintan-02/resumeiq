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


@pytest.fixture(autouse=True)
def _no_live_model(monkeypatch):
    """Tests never call the real model, even if ANTHROPIC_API_KEY is exported in the shell.

    The app reads the key once at import, so clearing the environment is not enough:
    the configured client is replaced too. Tests that need a model patch in a fake.
    """
    import resumeiq_api.app as app_module

    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(app_module, "COMPLETE", None)
