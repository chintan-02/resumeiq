import { MAX_JD_CHARS } from "@/lib/labels";
import { fail, forward, rateLimited } from "@/lib/proxy";

export async function POST(request: Request) {
  if (rateLimited(request, "fit-map", 20)) return fail(429, "Too many requests. Wait a minute and try again.");
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return fail(400, "Send JSON with a job_description field.");
  }
  const jd = (body as { job_description?: unknown })?.job_description;
  if (typeof jd !== "string" || !jd.trim()) return fail(400, "Paste a job description first.");
  if (jd.length > MAX_JD_CHARS) return fail(413, `Job descriptions are limited to ${MAX_JD_CHARS.toLocaleString()} characters.`);
  return forward("/v1/fit-map", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sample_id: "walkthrough", job_description: jd }),
  }, 10_000);
}
