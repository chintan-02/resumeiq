import Link from "next/link";

import { StatusChip } from "@/components/StatusChip";
import { loadSample } from "@/lib/sample";
import { REPORT_URL, SITE_URL } from "@/lib/site";

const steps = [
  {
    title: "Split your documents into evidence",
    body: "Each sentence and bullet is kept with its exact position, so every claim can be traced back to the line it came from.",
  },
  {
    title: "Read the job description safely",
    body: "Requirements are extracted by rules, not a model. Lines that look like instructions to an AI are ignored and shown to you.",
  },
  {
    title: "Map each requirement to proof",
    body: "Supported, partial or no supporting evidence found. “Contributed to the deployment” is not read as “led the deployment”.",
  },
  {
    title: "Coming next: grounded rewriting",
    body: "Drafted bullets will cite their evidence and be re-checked after every edit, before anything can be exported.",
  },
];

export default function Home() {
  const { fitMap } = loadSample();
  const preview = fitMap.results.slice(0, 5);
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

      <section className="mx-auto grid max-w-6xl items-center gap-14 px-6 py-20 lg:grid-cols-[1fr_1.1fr]">
        <div>
          <p className="font-mono text-xs uppercase tracking-[0.08em] text-accent">Evidence-grounded application copilot</p>
          <h1 className="mt-5 font-serif text-5xl leading-[1.02] tracking-tight sm:text-6xl">
            Tailor every application.
            <br />
            <em>Back every claim.</em>
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-ink-2">
            Map each job requirement to proof from your own work. Every match shows the exact line it came from, and a
            weaker claim is never read as a stronger one.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/demo" className="rounded-md bg-accent px-5 py-3.5 font-medium text-white hover:bg-accent-strong">
              Try it with a sample resume
            </Link>
            <a
              href={REPORT_URL}
              className="rounded-md border border-[#c9c6be] px-5 py-3.5 font-medium hover:bg-card"
            >
              Read the evaluation report
            </a>
          </div>
          <p className="mt-4 text-sm text-muted">
            Sample resumes with optional custom job descriptions. Nothing you paste is stored.
          </p>
        </div>

        <figure className="rounded-[10px] border border-hairline bg-card p-5" aria-label="Fit map from the sample">
          <div className="flex flex-wrap items-baseline justify-between gap-3 border-b border-[#efede8] pb-3.5">
            <div>
              <p className="text-xs text-muted">Fit map · live output for the sample</p>
              <p className="mt-0.5 font-semibold">{fitMap.job_title}</p>
            </div>
            <p className="text-xs text-muted">{fitMap.results.length} requirements</p>
          </div>
          <ul>
            {preview.map((r) => (
              <li key={r.requirement.id} className="flex flex-wrap items-center gap-3 border-b border-[#f2f0eb] py-3">
                <span className="min-w-0 flex-1 basis-56 text-sm">{r.requirement.text}</span>
                <StatusChip status={r.status} />
                <span className="min-w-16 rounded border border-hairline bg-soft px-1.5 py-0.5 text-center font-mono text-xs text-ink-2">
                  {r.citations[0]?.evidence_id ?? "none"}
                </span>
              </li>
            ))}
          </ul>
          <figcaption className="mt-3.5 text-xs text-muted">
            Each evidence id opens the exact line in the source document.
          </figcaption>
        </figure>
      </section>

      <section id="how" className="border-y border-hairline bg-card">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <h2 className="font-serif text-4xl tracking-tight">How it works</h2>
          <p className="mt-3 max-w-2xl text-ink-2">Deterministic checks first. No AI model reads your documents in this version.</p>
          <ol className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {steps.map((s, i) => (
              <li key={s.title} className="border-t border-ink pt-4">
                <p className="font-mono text-xs text-muted">{String(i + 1).padStart(2, "0")}</p>
                <h3 className="mt-2 text-lg font-semibold">{s.title}</h3>
                <p className="mt-2 text-[15px] leading-relaxed text-ink-2">{s.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section id="evaluation" className="mx-auto grid max-w-6xl gap-10 px-6 py-20 lg:grid-cols-[1fr_1.4fr]">
        <div>
          <h2 className="font-serif text-4xl tracking-tight">Measured, not claimed</h2>
          <p className="mt-3 leading-relaxed text-ink-2">
            Matching is evaluated on a separate labelled set, never on the demo sample. Quality numbers will appear here
            once the labels have had a human review.
          </p>
          <a href={REPORT_URL} className="mt-5 inline-block font-medium text-accent hover:text-accent-strong">
            Read the current report →
          </a>
        </div>
        <ul className="grid gap-4 text-[15px] leading-relaxed text-ink-2 sm:grid-cols-2">
          <li className="rounded-[10px] border border-hairline bg-card p-5">
            <p className="font-semibold text-ink">Separate dev and test sets</p>
            Thresholds are tuned on one set of candidates and job families and scored on another.
          </li>
          <li className="rounded-[10px] border border-hairline bg-card p-5">
            <p className="font-semibold text-ink">Keyword-trap cases</p>
            Cases where the right word appears but the evidence supports a weaker claim.
          </li>
          <li className="rounded-[10px] border border-hairline bg-card p-5">
            <p className="font-semibold text-ink">Retrieval and judgment measured apart</p>
            Evidence recall@k shows whether the right line was found; macro-F1 shows whether the verdict was right.
          </li>
          <li className="rounded-[10px] border border-hairline bg-card p-5">
            <p className="font-semibold text-ink">Reproducible in one command</p>
            CI fails if the committed report and a fresh run disagree.
          </li>
        </ul>
      </section>
    </>
  );
}
