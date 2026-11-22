import { NextResponse } from "next/server";

import { MAX_JD_CHARS } from "@/lib/labels";

// Backend-for-frontend: the browser only talks to this route; the API URL stays server-side.
const API_URL = process.env.RESUMEIQ_API_URL;
const WINDOW_MS = 60_000;
const MAX_REQUESTS_PER_WINDOW = 20;
const hits = new Map<string, number[]>();

function rateLimited(ip: string): boolean {
  // Best effort, per server instance. The API's own instance cap is the hard limit.
  const now = Date.now();
  const recent = (hits.get(ip) ?? []).filter((t) => now - t < WINDOW_MS);
  recent.push(now);
  hits.set(ip, recent);
  if (hits.size > 5_000) hits.clear();
  return recent.length > MAX_REQUESTS_PER_WINDOW;
}

const fail = (status: number, detail: string) => NextResponse.json({ detail }, { status });

export async function POST(request: Request) {
  if (!API_URL) return fail(503, "Live matching is not configured here. The sample result is still available.");

  const ip = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "unknown";
  if (rateLimited(ip)) return fail(429, "Too many requests. Wait a minute and try again.");

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return fail(400, "Send JSON with a job_description field.");
  }
  const jd = (body as { job_description?: unknown })?.job_description;
  if (typeof jd !== "string" || !jd.trim()) return fail(400, "Paste a job description first.");
  if (jd.length > MAX_JD_CHARS) return fail(413, `Job descriptions are limited to ${MAX_JD_CHARS.toLocaleString()} characters.`);

  try {
    const upstream = await fetch(`${API_URL.replace(/\/$/, "")}/v1/fit-map`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sample_id: "walkthrough", job_description: jd }),
      signal: AbortSignal.timeout(10_000),
      cache: "no-store",
    });
    const data = await upstream.json();
    if (!upstream.ok) return fail(upstream.status, typeof data?.detail === "string" ? data.detail : "The job description could not be processed.");
    return NextResponse.json(data, { headers: { "Cache-Control": "no-store" } });
  } catch {
    return fail(503, "Live matching is unavailable right now. The sample result is still available.");
  }
}
