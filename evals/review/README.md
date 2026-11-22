# Label review (about 1 hour)

Keep `evals/LABELING_GUIDE.md` open while you review.

## You: `review_primary.csv` (all 54 cases)

1. Open it in Numbers, Excel or Google Sheets.
2. For each row, read the requirement, its required level and the evidence pool, then the draft label.
3. In `your_status`:
   - **agree:** write `ok`
   - **disagree:** write `supported`, `partial` or `not_found`, put the supporting evidence ids in
     `your_evidence_ids` (for example `C4-E05`), and add a one-line `note`.
4. Save or export as **CSV (UTF-8)** with the same file name, in this folder.

## Second reviewer: `review_second_blind.csv` (23 trap and ambiguous cases)

Send them this file and `evals/LABELING_GUIDE.md` only. Don't show them the draft labels or your answers.
They fill `status` (and `evidence_ids` and `note` if useful) and send it back; save it here as CSV.

## Then

```bash
bash evals/finish_milestone1.sh
```

This applies your review, reports agreement (Cohen's kappa) with the second reviewer, runs the
embedding comparison and all checks. Settle any disagreements it lists, update `review_primary.csv`,
and run it again.
