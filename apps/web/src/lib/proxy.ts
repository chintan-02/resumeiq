import { NextResponse } from "next/server";

// Shared by the backend-for-frontend routes. The browser only talks to these
// routes; the API URL stays on the server.
export const API_URL = process.env.RESUMEIQ_API_URL?.replace(/\/$/, "");

const WINDOW_MS = 60_000;
const hits = new Map<string, number[]>();

/** Best effort, per server instance. The API's instance cap and budgets are the hard limits. */
export function rateLimited(request: Request, bucket: string, perMinute: number): boolean {
  const ip = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "unknown";
  const key = `${bucket}:${ip}`;
  const now = Date.now();
  const recent = (hits.get(key) ?? []).filter((t) => now - t < WINDOW_MS);
  recent.push(now);
  hits.set(key, recent);
  if (hits.size > 5_000) hits.clear();
  return recent.length > perMinute;
}

export const fail = (status: number, detail: string) => NextResponse.json({ detail }, { status });

/** Forward to the API and pass its JSON (or a safe error) back. */
export async function forward(path: string, init: RequestInit, timeoutMs = 15_000): Promise<NextResponse> {
  if (!API_URL) return fail(503, "Live matching is not configured here. The sample result is still available.");
  try {
    const upstream = await fetch(`${API_URL}${path}`, { ...init, signal: AbortSignal.timeout(timeoutMs), cache: "no-store" });
    const data = await upstream.json();
    if (!upstream.ok) {
      const detail = typeof data?.detail === "string" ? data.detail : "The request could not be processed.";
      return fail(upstream.status, detail);
    }
    return NextResponse.json(data, { headers: { "Cache-Control": "no-store" } });
  } catch {
    return fail(503, "The service is unavailable right now. Try again in a minute.");
  }
}
