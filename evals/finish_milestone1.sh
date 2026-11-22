#!/usr/bin/env bash
# Finish Milestone 1 in one go, after the review sheets are filled in.
# Applies the label review, runs the embedding comparison, rebuilds the report
# and the walkthrough, and runs every check. Run from anywhere inside the repo.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

if [ ! -d .venv-v2 ]; then python3 -m venv .venv-v2; fi
source .venv-v2/bin/activate

echo "== 1/5 Apply label review"
python evals/review/apply_review.py

echo "== 2/5 Install embeddings extra (first run downloads PyTorch and a ~90 MB model)"
pip install -q -e "apps/api[dev,embeddings]"

echo "== 3/5 Re-tune on dev and evaluate all four matchers"
python evals/run_baseline.py --matchers keyword keyword-rules embedding embedding-rules

echo "== 4/5 Rebuild the precomputed walkthrough"
python -m resumeiq_api.build_walkthrough

echo "== 5/5 Tests and reproducibility check"
(cd apps/api && python -m pytest -q)
python evals/run_baseline.py --check

echo
git status --short
echo
echo "All checks passed. Commit with:"
echo '  git add evals apps/api/src/resumeiq_api'
echo '  git commit -m "feat(evals): apply human label review and add embedding comparison"'
echo '  git push origin v2'
