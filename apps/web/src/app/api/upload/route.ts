import { MAX_JD_CHARS, MAX_UPLOAD_BYTES } from "@/lib/labels";
import { fail, forward, rateLimited } from "@/lib/proxy";

// The resume passes straight through to the API in memory. Nothing is stored here.
export async function POST(request: Request) {
  if (rateLimited(request, "upload", 6)) return fail(429, "Too many uploads. Wait a minute and try again.");
  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return fail(400, "Send a resume file and a job description.");
  }
  const resume = form.get("resume");
  const jd = form.get("job_description");
  if (!(resume instanceof File) || resume.size === 0) return fail(400, "Choose a resume file.");
  if (resume.size > MAX_UPLOAD_BYTES) return fail(413, "Files are limited to 2 MB.");
  if (typeof jd !== "string" || !jd.trim()) return fail(400, "Paste a job description first.");
  if (jd.length > MAX_JD_CHARS) return fail(413, `Job descriptions are limited to ${MAX_JD_CHARS.toLocaleString()} characters.`);

  const out = new FormData();
  out.set("resume", resume, resume.name);
  out.set("job_description", jd);
  return forward("/v1/fit-map/upload", { method: "POST", body: out }, 20_000);
}
