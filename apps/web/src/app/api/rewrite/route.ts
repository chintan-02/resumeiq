import { fail, forward, rateLimited } from "@/lib/proxy";

export async function GET() {
  return forward("/v1/rewrite/status", { method: "GET" }, 5_000);
}

export async function POST(request: Request) {
  if (rateLimited(request, "rewrite", 6)) return fail(429, "Too many drafts. Wait a minute and try again.");
  const body = await request.text();
  if (body.length > 4_000) return fail(413, "That request is too large.");
  return forward("/v1/rewrite", { method: "POST", headers: { "Content-Type": "application/json" }, body }, 25_000);
}
