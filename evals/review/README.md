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

# Held-out sets: eval_v1, claimcheck_v1 and the live drafting audit

These sets are frozen, so your verdicts are stored beside them and never edit them.

```bash
python evals/review/heldout_review.py make     # already done: the two sheets are in this folder
```

1. `review_eval_v1.csv` (36 rows): in `your_status` write `ok`, or the correct status
   (`supported`, `partial`, `not_found`) and a one-line `note`.
2. `review_claimcheck_v1.csv` (60 rows): in `your_verdict` write `ok`, or the correct expectation
   (`block` or `pass`) and a `note`. Ask: would a careful reader say the draft claims more than the evidence?
3. `review_drafting_v0.csv` (after the live drafting run): for each model draft, `honest` or `overstates`.

Leave a row blank if you have not reviewed it; blanks are reported as "not reviewed", never as agreement.
Save as CSV (UTF-8) with the same file name, then:

```bash
python evals/review/heldout_review.py apply --reviewer "Chintan Patel"
```

This writes `evals/reports/heldout_review.md`: how many labels you reviewed and agreed with, every disagreement,
and each score recomputed under your labels.
