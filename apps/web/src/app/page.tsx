import Link from "next/link";

import { StatusChip } from "@/components/StatusChip";
import { SummaryBar } from "@/components/SummaryBar";
import { sectionBullets } from "@/lib/document";
import { loadSample } from "@/lib/sample";
import { REPORT_URL, SITE_URL } from "@/lib/site";

const steps = [
  {
    title: "Pulls out the real requirements",
    body: "Works on postings pasted straight from a job board. Pay, benefits and legal text are left out, and lines that try to instruct an AI are ignored and shown to you.",
  },
  {
    title: "Quotes the line that proves it",
    body: "Every status points to an exact sentence from your resume or project write-up, never a paraphrase. If nothing supports a requirement, it says so.",
  },
  {
    title: "Weighs how strong the proof is",
    body: "Knowing a tool, using it, building with it and owning it are different claims. A job that asks you to lead a deployment needs more than “contributed to”.",
  },
];

const evaluation = [
  {
    title: "Separate dev and test sets",
    body: "Thresholds are tuned on one set of candidates and job families and scored on another.",
  },
  {
    title: "Keyword-trap cases",
    body: "Cases where the right word appears but the evidence supports a weaker claim.",
  },
  {
    title: "Retrieval and judgment measured apart",
    body: "Evidence recall@k shows whether the right line was found; macro-F1 shows whether the verdict was right.",
  },
  {
    title: "Reproducible in one command",
    body: "CI fails if the committed report and a fresh run disagree.",
  },
];

export default function Home() {
  const { documents, fitMap } = loadSample();
  const resume = documents.find((d) => d.kind === "resume")!;
  const docker = fitMap.results.find((r) => /docker/i.test(r.requirement.text)) ?? fitMap.results[0];
  const quote = docker.citations[0]?.quote ?? "";
  const heroLines = sectionBullets(resume.text, "Experience").slice(0, 3);
  const preview = ["supported", "partial", "not_found"]
    .flatMap((s) => fitMap.results.filter((r) => r.status === s).slice(0, s === "supported" ? 2 : 1))
    .slice(0, 4);

  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    name: "ResumeIQ",
    url: SITE_URL,
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    description: "Maps job requirements to exact quotes from a candidate's own documents.",
    author: { "@type": "Person", name: "Chintan Patel" },
  };

  return (
    <>
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }} />

      <section className="mx-auto grid max-w-6xl items-center gap-16 px-6 pb-24 pt-20 sm:px-8 lg:grid-cols-[1.05fr_1fr] lg:pt-28">
        <div className="space-y-7">
          <p className="flex items-center gap-2.5 font-mono text-xs uppercase tracking-[0.08em] text-mint-ink">
            <span aria-hidden="true" className="size-1.5 rounded-full bg-mint" />
            Evidence-backed applications
          </p>
          <h1 className="text-[2.75rem] font-semibold leading-[1.03] tracking-[-0.035em] text-balance sm:text-6xl">
            Match every requirement to a line you actually wrote.
          </h1>
          <p className="max-w-xl text-lg leading-relaxed text-muted text-pretty sm:text-[19px]">
            Paste a job description. ResumeIQ finds the exact sentence in your resume that proves each requirement, and
            tells you honestly when nothing does.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link
              href="/demo#paste"
              className="flex min-h-12 items-center gap-2.5 rounded-xl bg-mint px-5 font-semibold text-mint-deep hover:bg-mint-ink"
            >
              Paste a job description
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                <path d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </Link>
            <Link href="/demo" className="flex min-h-12 items-center rounded-xl border border-line-2 px-5 font-medium hover:bg-panel">
              See the sample
            </Link>
          </div>
          <p className="flex flex-wrap gap-x-6 gap-y-1 text-[13px] text-subtle">
            <span>No sign-up</span>
            <span>Nothing you paste is stored</span>
            <span>Open source</span>
          </p>
        </div>

        <figure aria-label="Example: a requirement matched to the resume line that proves it" className="flex flex-col">
          <div className="space-y-3 rounded-2xl border border-line bg-panel px-6 py-5 shadow-[0_30px_80px_-30px_rgba(0,0,0,0.8)]">
            <div className="flex items-center justify-between gap-3">
              <span className="font-mono text-[11px] uppercase tracking-[0.08em] text-subtle">The job asks</span>
              <StatusChip status={docker.status} compact />
            </div>
            <p className="text-xl font-medium">{docker.requirement.text}</p>
          </div>
          <div aria-hidden="true" className="mx-auto h-11 w-0.5 bg-mint/60" />
          <div className="space-y-2.5 rounded-2xl bg-paper px-7 py-6 text-paper-ink shadow-[0_30px_80px_-30px_rgba(0,0,0,0.9)]">
            <div className="flex items-baseline justify-between gap-3">
              <span className="font-bold">Jordan Avery</span>
              <span className="text-xs text-paper-muted">Contact details hidden</span>
            </div>
            <p className="pt-1 text-[13px] font-semibold text-paper-2">Junior Data Scientist · Prairie Grocers Co-op · 2024–2026</p>
            {heroLines.map((line) =>
              line === quote ? (
                <p key={line} className="-mx-2.5 rounded-md bg-hl px-2.5 py-1.5 text-[13.5px] leading-relaxed text-hl-ink shadow-[inset_3px_0_0_#1f9e68]">
                  {line}
                </p>
              ) : (
                <p key={line} className="text-[13.5px] leading-relaxed text-paper-muted">
                  {line}
                </p>
              ),
            )}
            <figcaption className="pt-1 font-mono text-[11px] text-[#1f6e4c]">Exact quote · shows building</figcaption>
          </div>
        </figure>
      </section>

      <section id="how" className="border-y border-line bg-bg-2">
        <div className="mx-auto max-w-6xl space-y-11 px-6 py-20 sm:px-8">
          <h2 className="text-3xl font-semibold tracking-[-0.025em] sm:text-4xl">How it reads a job</h2>
          <ol className="grid gap-8 md:grid-cols-3">
            {steps.map((s, i) => (
              <li key={s.title} className="space-y-3 border-t border-line-2 pt-6">
                <p className="font-mono text-[13px] text-mint-ink">{String(i + 1).padStart(2, "0")}</p>
                <h3 className="text-xl font-semibold">{s.title}</h3>
                <p className="text-[15px] leading-relaxed text-muted">{s.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section aria-labelledby="sample-heading" className="mx-auto max-w-6xl space-y-6 px-6 py-24 sm:px-8">
        <div className="flex flex-wrap items-end justify-between gap-5">
          <div className="space-y-2.5">
            <p className="font-mono text-xs uppercase tracking-[0.08em] text-subtle">Sample · synthetic data</p>
            <h2 id="sample-heading" className="text-3xl font-semibold tracking-[-0.025em] sm:text-4xl">
              {fitMap.job_title.replace(" (fictional)", "")}
            </h2>
            <p className="text-[15px] text-muted">A synthetic resume and project write-up against a fictional posting</p>
          </div>
          <Link href="/demo" className="flex min-h-11 items-center rounded-xl border border-line-2 px-4 font-medium hover:bg-panel">
            Open the full sample
          </Link>
        </div>
        <SummaryBar summary={fitMap.summary} total={fitMap.results.length} />
        <ul className="grid gap-2.5 md:grid-cols-2">
          {preview.map((r) => (
            <li
              key={r.requirement.id}
              className={`flex min-h-16 items-center justify-between gap-4 rounded-2xl border bg-panel px-5 py-4 ${
                r.status === "not_found" ? "border-dashed border-line-2" : "border-line"
              }`}
            >
              <span className="text-[15.5px] leading-snug">{r.requirement.text}</span>
              <StatusChip status={r.status} compact />
            </li>
          ))}
        </ul>
      </section>

      <section id="evaluation" className="border-t border-line bg-bg-2">
        <div className="mx-auto grid max-w-6xl gap-12 px-6 py-20 sm:px-8 lg:grid-cols-[1fr_1.4fr]">
          <div className="space-y-4">
            <h2 className="text-3xl font-semibold tracking-[-0.025em] sm:text-4xl">Measured, not claimed</h2>
            <p className="leading-relaxed text-muted">
              Matching is evaluated on a separate labelled set, never on the demo sample. Quality numbers will appear
              here once the labels have had a human review.
            </p>
            <a href={REPORT_URL} className="inline-flex min-h-11 items-center font-medium text-mint-ink hover:text-mint">
              Read the current report →
            </a>
          </div>
          <ul className="grid gap-4 sm:grid-cols-2">
            {evaluation.map((e) => (
              <li key={e.title} className="space-y-2 rounded-2xl border border-line bg-panel p-6">
                <p className="font-semibold">{e.title}</p>
                <p className="text-[15px] leading-relaxed text-muted">{e.body}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </>
  );
}
