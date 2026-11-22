# ResumeIQ v2 · Milestone 2: live sample demo

**Finish line:** a public website that shows the fit map for a synthetic resume, accepts a pasted job
description, and cites the exact source line behind every status. No AI model is called, so it costs
nothing per visitor.

## What is in this milestone

| Piece | Where | Notes |
| --- | --- | --- |
| Landing page | `apps/web/src/app/page.tsx` | Static HTML; preview uses the real walkthrough output |
| Demo | `apps/web/src/app/demo/` | Fit map, evidence panel, highlighted source lines, custom job description |
| Backend-for-frontend | `apps/web/src/app/api/fit-map/route.ts` | Browser never calls the API directly; size and rate limits |
| Offline fallback | `apps/web/src/data/sample/` | Copy of the API walkthrough; CI fails if it drifts |
| SEO | `sitemap.ts`, `robots.ts`, `not-found.tsx`, per-page metadata | Canonical URLs, JSON-LD without invented ratings |
| Security headers | `apps/web/next.config.ts` | Static CSP on prerendered pages; previews are `noindex` |
| API container | `apps/api/Dockerfile` | Non-root, no torch; CI builds and smoke-tests it |

Measured locally (Lighthouse, mobile): Performance 93–95, Accessibility 100, Best Practices 100, SEO 100.
LCP was 2.8–3.0 s under simulated slow 4G, above the 2.5 s target; re-measure on the deployed site.

## Run it locally

```bash
# Terminal 1: API
source .venv-v2/bin/activate
uvicorn resumeiq_api.app:app --port 8000

# Terminal 2: web
cd apps/web
npm install
RESUMEIQ_API_URL=http://127.0.0.1:8000 npm run dev
# open http://localhost:3000
```

## Deploy (free tiers)

### 1. API on Google Cloud Run

```bash
gcloud run deploy resumeiq-api \
  --source apps/api \
  --region us-west1 \
  --allow-unauthenticated \
  --max-instances 2 \
  --memory 512Mi \
  --concurrency 40
```

Copy the service URL it prints (ends in `.run.app`). `--max-instances 2` is the hard cost cap.

### 2. Web on Vercel

1. vercel.com → **Add New → Project** → import `chintan-02/smart-resume-classifier`.
2. **Root Directory:** `apps/web`. Framework: Next.js (detected). **Production Branch:** `v2`
   (Settings → Git), so `main` stays untouched until the release merge.
3. Environment variables:
   - `RESUMEIQ_API_URL` = the Cloud Run URL from step 1
   - `NEXT_PUBLIC_SITE_URL` = the final site URL, e.g. `https://resumeiq.chintanpatel.dev`
4. Deploy. Optional: add the domain under **Settings → Domains** and create the CNAME it shows.

### 3. After deploying

- [ ] `/demo` loads and selecting a requirement highlights the right line
- [ ] Pasting a job description returns a fit map; stopping the API shows the fallback message
- [ ] `curl -I https://<site>/nope` returns 404; `/robots.txt` and `/sitemap.xml` use the real domain
- [ ] Lighthouse mobile on the live URL; fix LCP if it is still above 2.5 s
- [ ] Submit the sitemap in Google Search Console
