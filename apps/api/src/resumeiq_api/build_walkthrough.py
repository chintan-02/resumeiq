"""Regenerate the precomputed walkthrough fit map.

Run after changing matching rules or tuned thresholds:

    python -m resumeiq_api.build_walkthrough

A test fails if the committed file and a fresh computation disagree.
"""

from __future__ import annotations

import json

from .fitmap import build_fit_map
from .samples import load_samples


def render(sample_id: str = "walkthrough") -> str:
    sample = load_samples()[sample_id]
    fit_map = build_fit_map(sample.documents, sample.job_title, job_text=sample.job_text)
    return json.dumps(fit_map.model_dump(mode="json"), indent=2) + "\n"


def main() -> None:
    sample = load_samples()["walkthrough"]
    sample.precomputed_path.write_text(render(), encoding="utf-8")
    print(f"Wrote {sample.precomputed_path}")


if __name__ == "__main__":
    main()
