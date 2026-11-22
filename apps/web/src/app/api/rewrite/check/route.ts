import { fail, forward, rateLimited } from "@/lib/proxy";

export async function POST(request: Request) {
  if (rateLimited(request, "check", 30)) return fail(429, "Too many checks. Wait a minute and try again.");
  const body = await request.text();
  if (body.length > 4_000) return fail(413, "That request is too large.");
  return forward("/v1/rewrite/check", { method: "POST", headers: { "Content-Type": "application/json" }, body }, 8_000);
}
