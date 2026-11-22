# Operations

How ResumeIQ is watched in production, and what to do when something breaks. Project `resumeiq-chintan-2026`,
service `resumeiq-api`, region `us-west1`, site `resumeiq-chintan.vercel.app`.

## What is logged

The API writes one JSON line per request to stdout. Cloud Run sends it to Cloud Logging.

| Field | Example | Notes |
| --- | --- | --- |
| `severity` | `INFO` | `WARNING` for 5xx responses, `ERROR` for crash reports |
| `route` | `/v1/samples/{sample_id}/fit-map` | The route template, never the raw URL |
| `method`, `status`, `latency_ms` | `POST`, `200`, `41.2` | |
| `request_id` | `4693998c…` | Also returned as the `X-Request-ID` response header |
| `trace_id` | `105445aa…` | From Cloud Run's trace header, to join with platform logs |

Never logged: request or response bodies, query strings, uploaded file names, IP addresses, user agents. Uvicorn's
own access log is turned off (`--no-access-log`) because it prints IPs and full URLs.

Cloud Run also keeps its own platform request log (outside the app) with the caller's IP and URL. No user content
reaches it, because resumes and job descriptions only travel in POST bodies. It is kept for the project's default
retention (30 days).

**Read the logs:** Cloud Console → Logging → Logs Explorer, query:

```text
resource.type="cloud_run_revision"
resource.labels.service_name="resumeiq-api"
jsonPayload.route:*
```

Slow requests: add `jsonPayload.latency_ms > 2000`. Errors: replace the last line with `severity>=WARNING`.

## Error tracking

An unhandled exception becomes:

1. A safe `500` for the caller: `Something went wrong on our side (reference 1a2b3c4d)`, with the full id in
   `request_id`.
2. One `ERROR` log line tagged as a Cloud Error Reporting event, with the stack frames and the exception type. The
   exception message is replaced by `[message hidden]`, because it could quote user input.

Cloud Error Reporting groups these automatically, with no SDK or extra service. **Turn on notifications (once):**
Console → Error Reporting → **Configure notifications** → add your email. You get one email per new error group.

To find a user's error from a reference they send: search Logs Explorer for `jsonPayload.request_id:"1a2b3c4d"`.

## Uptime check (set up once)

Checks `/health` from three regions every 15 minutes. Uptime checks are within Cloud Monitoring's free allowance at
this frequency.

```bash
gcloud monitoring uptime create resumeiq-api-health \
  --resource-type=uptime-url \
  --resource-labels=host=resumeiq-api-89542555496.us-west1.run.app,project_id=resumeiq-chintan-2026 \
  --protocol=https --path=/health --period=15 \
  --matcher-content='"status":"ok"' --matcher-type=contains-string
```

Optionally, check the site too:

```bash
gcloud monitoring uptime create resumeiq-site-demo \
  --resource-type=uptime-url \
  --resource-labels=host=resumeiq-chintan.vercel.app,project_id=resumeiq-chintan-2026 \
  --protocol=https --path=/demo --period=15
```

If a flag is rejected by your gcloud version, create the same check in the console: Monitoring → Uptime checks →
**Create uptime check** (protocol HTTPS, hostname as above, path `/health`, frequency 15 minutes, response content
contains `"status":"ok"`).

**Alert on failure:** Monitoring → Uptime checks → `resumeiq-api-health` → **Create alert**. Add an email
notification channel. The default (fails from 2 or more regions for 5 minutes) is right for this service.

Note: each check is a real request, so it may start a Cloud Run instance. At 15-minute intervals this is a few
seconds of CPU per hour, well inside the free tier.

## Rate limits

| Route (POST) | Bucket | Per client per minute, per instance |
| --- | --- | --- |
| `/v1/fit-map` | `fit-map` | 60 |
| `/v1/fit-map/upload` | `upload` | 30 |
| `/v1/rewrite` | `rewrite` | 20 |
| `/v1/rewrite/check` | `check` | 60 |

Reads (`GET`) and `/health` are never limited. Over the limit: `429` with `Retry-After`.

- **Who is "a client":** the address Google's front end appends as the last entry of `X-Forwarded-For`. Entries a
  caller sends land to its left and are ignored, so spoofing the header does not bypass the limit. Addresses are
  only held in memory, as hashes.
- **Why the site is not throttled:** the website's server calls the API from Vercel's addresses, so site visitors
  share a few API clients. Per-visitor limits live in the site (`apps/web/src/lib/proxy.ts`); the API limits stop
  direct abuse and sit well above site traffic.
- **Per instance:** limits are in memory, and Cloud Run runs at most 2 instances, so the true ceiling is up to twice
  the table. Model cost is capped separately by the daily drafting budget.

Configuration (Cloud Run environment variables, no code change):

| Variable | Default | Use |
| --- | --- | --- |
| `RESUMEIQ_RATE_LIMITS` | `fit-map=60,upload=30,rewrite=20,check=60` | Change any limit |
| `RESUMEIQ_TRUSTED_HOPS` | `1` | Set to `2` if a load balancer is put in front of Cloud Run |
| `RESUMEIQ_REWRITE_DAILY_LIMIT` | `40` | Model drafts per instance per UTC day |

Example: `gcloud run services update resumeiq-api --region us-west1 --update-env-vars RESUMEIQ_RATE_LIMITS=upload=10`

## Runbook

| Symptom | Check | Likely fix |
| --- | --- | --- |
| Uptime alert for the API | `curl https://resumeiq-api-89542555496.us-west1.run.app/health` | If it fails, Cloud Run → Revisions: roll back to the previous revision (**Manage traffic**) |
| Site works, live matching says "unavailable" | API health, then Vercel env `RESUMEIQ_API_URL` | Fix the URL in Vercel and redeploy |
| Error Reporting email | Open the group, read the stack, find a `request_id` | Reproduce locally with the same route; fix, test, deploy |
| Many `429`s in logs | Logs Explorer: `jsonPayload.status=429`, group by route | Abuse: leave it. Real users: raise that bucket with `RESUMEIQ_RATE_LIMITS` |
| Bill alert | Billing → Reports, by service | Lower `--max-instances` or `RESUMEIQ_REWRITE_DAILY_LIMIT`; check for 429 spikes |
| Deploy broke something | Cloud Run → Revisions | Send 100% traffic to the last good revision, then fix forward |
