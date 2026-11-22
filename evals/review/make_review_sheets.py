"""Create the label-review spreadsheets from the dataset.

Two sheets, opened in Numbers, Excel or Google Sheets and saved back as CSV:

* review_primary.csv: every case with the draft label shown. You confirm or correct it.
* review_second_blind.csv: only trap and ambiguous cases, with NO draft label, so the
  second reviewer labels independently. Showing them the answer would anchor them.

Run from the repository root:  python evals/review/make_review_sheets.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "evals" / "datasets" / "eval_v0.json"
OUT = ROOT / "evals" / "review"
LEVELS = {1: "L1 aware", 2: "L2 used", 3: "L3 built", 4: "L4 owned"}


def rows(data: dict) -> list[dict]:
    reqs = {r["id"]: r for j in data["jobs"].values() for r in j["requirements"]}
    out = []
    for case in data["cases"]:
        req = reqs[case["requirement"]]
        pool = data["candidates"][case["candidate"]]["evidence"]
        out.append(
            {
                "case_id": case["id"],
                "requirement": req["text"],
                "required_level": LEVELS[req["required_level"]],
                "evidence_pool": "\n".join(f"{e['id']}: {e['text']}" for e in pool),
                "draft_status": case["gold_status"],
                "draft_evidence_ids": " ".join(case["gold_evidence_ids"]),
                "draft_rationale": case["rationale"],
                "trap": "yes" if case["trap"] else "",
                "ambiguous": "yes" if case["ambiguous"] else "",
            }
        )
    return out


def write(path: Path, records: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    data = json.loads(DATASET.read_text(encoding="utf-8"))
    records = rows(data)
    primary = [{**r, "your_status": "", "your_evidence_ids": "", "note": ""} for r in records]
    write(OUT / "review_primary.csv", primary, list(primary[0]))
    blind_fields = ["case_id", "requirement", "required_level", "evidence_pool", "status", "evidence_ids", "note"]
    blind = [{**r, "status": "", "evidence_ids": "", "note": ""} for r in records if r["trap"] or r["ambiguous"]]
    write(OUT / "review_second_blind.csv", blind, blind_fields)
    print(f"Wrote {len(primary)} rows to review_primary.csv and {len(blind)} to review_second_blind.csv")


if __name__ == "__main__":
    main()
