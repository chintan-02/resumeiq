# ResumeIQ v2 · Milestone 3: your resume, grounded drafts, approval

**Finish line:** upload your own resume, see the fit map for any job description, draft a stronger bullet for a
requirement, and approve it only after a rule-based check confirms the draft says nothing your evidence does not.

## What is in this milestone

| Piece | Where | Notes |
| --- | --- | --- |
| Resume upload | `apps/api/src/resumeiq_api/uploads.py`, `POST /v1/fit-map/upload` | PDF (text-based), DOCX, TXT. 2 MB, 6 pages. Read in memory, never stored or logged |
| Contact masking | `privacy.py` (ported from v0.9 `privacy_tools`) | Email, phone and profile links are masked before matching, display or any model call |
| Grounded drafting | `rewrite.py`, `POST /v1/rewrite` | The model sees one requirement and the 1–3 cited lines, nothing else |
| Claim checker | `check_claim` in `rewrite.py`, `POST /v1/rewrite/check` | Blocks stronger verbs than the matching line, numbers not in the evidence, and new tools |
| Approval | `approval_token` + `RewritePanel.tsx` | Bound to a hash of the exact text and its evidence; any edit needs a fresh check |
| Cost control | `DailyBudget` in `rewrite.py` | No key, no calls. With a key: a daily call cap per instance, 200 output tokens per call, one retry |

### How a draft is made

1. The user opens a requirement that has evidence and asks for a draft.
2. If AI drafting is on, the model gets the requirement and the cited lines (masked, fenced as untrusted data)
   and must answer with one bullet.
3. `check_claim` reads the draft without trusting it. It fails when:
   - the verb is stronger than the line the bullet is about ("contributed to" → "led", or borrowing "built" from a
     different line),
   - a number appears that is not in the evidence,
   - a named tool appears that is not in the evidence.
4. A failed draft is retried once with the problems listed. If it fails again, or the budget is spent, or no key is
   set, the user gets the rule-based shape: the most relevant line, a `[Your verb]` placeholder for a weak opening and
   `[add measurable result]`.
5. Approve is enabled only with a token for the exact text. Editing clears it until **Check again** passes.

### Why no LangGraph

The original plan named LangGraph for the pilot. The flow that shipped is draft → check → one retry → fallback,
about twenty lines of plain code with a deterministic checker. A graph framework would add a dependency and a layer
to debug without adding a capability. Revisit it if the flow grows branches (for example, asking the user a
clarifying question before drafting).

## Turn AI drafting on (optional)

The site works fully without this: drafts fall back to the rule-based shape.

1. Create an API key in the Anthropic Console and **set a monthly spend limit there** (for example $5). That limit
   is the hard stop; the backend budget below is the second line.
2. Store the key as a secret and give only the API's runtime account access to it:

```bash
gcloud services enable secretmanager.googleapis.com
printf "%s" "PASTE_KEY_HERE" | gcloud secrets create anthropic-api-key --data-file=-
gcloud secrets add-iam-policy-binding anthropic-api-key --member="serviceAccount:resumeiq-api-runtime@resumeiq-chintan-2026.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
gcloud run services update resumeiq-api --region us-west1 --set-secrets=ANTHROPIC_API_KEY=anthropic-api-key:latest --set-env-vars=RESUMEIQ_REWRITE_DAILY_LIMIT=40
```

3. Check: `curl https://<api>/v1/rewrite/status` should show `"model_enabled": true`.

The daily cap is per instance, so the worst case per day is `max instances × RESUMEIQ_REWRITE_DAILY_LIMIT` calls
(2 × 40 = 80 short calls). The model defaults to `claude-haiku-5-5`; override with `RESUMEIQ_LLM_MODEL`.

To turn it off again: `gcloud run services update resumeiq-api --region us-west1 --remove-secrets=ANTHROPIC_API_KEY`.

## Known limits

- Scanned PDFs have no text layer and are rejected with a message; OCR is out of scope.
- The tool list in the checker is finite. A tool it does not know can slip into a model draft; the user still has to
  approve every bullet, and the drafted text is shown next to the evidence.
- The daily budget lives in memory, so it resets when an instance restarts. The Anthropic spend limit is the hard cap.
- Names are not masked on screen (the user sees their own resume, and nothing is stored). Drafting sends only the
  cited lines, with contact details masked; a name inside a cited sentence would be sent.
