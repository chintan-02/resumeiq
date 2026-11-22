"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { StatusChip } from "@/components/StatusChip";
import { segmentDocument } from "@/lib/highlight";
import { LEVEL_LABEL, MAX_JD_CHARS } from "@/lib/labels";
import type { FitMap, SourceDocument } from "@/lib/types";

interface Props {
  documents: SourceDocument[];
  sampleJobText: string;
  sampleFitMap: FitMap;
}

export function DemoWorkspace({ documents, sampleJobText, sampleFitMap }: Props) {
  const [fitMap, setFitMap] = useState<FitMap>(sampleFitMap);
  const [selectedId, setSelectedId] = useState(sampleFitMap.results[0]?.requirement.id ?? "");
  const [jobText, setJobText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [usingSample, setUsingSample] = useState(true);
  const sourceRef = useRef<HTMLDivElement>(null);
  const docsRef = useRef<HTMLDivElement>(null);

  const selected = fitMap.results.find((r) => r.requirement.id === selectedId) ?? fitMap.results[0];
  const citations = useMemo(() => selected?.citations ?? [], [selected]);

  // Scroll each document box (not the page) so the first highlighted quote is visible.
  useEffect(() => {
    docsRef.current?.querySelectorAll("pre").forEach((pre) => {
      const mark = pre.querySelector("mark");
      pre.scrollTop = mark ? Math.max(0, mark.offsetTop - 24) : 0;
    });
  }, [citations]);

  async function mapCustomJob(event: React.FormEvent) {
    event.preventDefault();
    if (!jobText.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/fit-map", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_description: jobText }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Matching failed. Try again.");
      setFitMap(body as FitMap);
      setSelectedId((body as FitMap).results[0]?.requirement.id ?? "");
      setUsingSample(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Matching failed. Try again.");
    } finally {
      setBusy(false);
    }
  }

  function resetToSample() {
    setFitMap(sampleFitMap);
    setSelectedId(sampleFitMap.results[0]?.requirement.id ?? "");
    setUsingSample(true);
    setError(null);
  }

  function select(id: string) {
    setSelectedId(id);
    // On narrow screens the evidence panel sits below the list; bring it into view.
    if (window.matchMedia("(max-width: 1023px)").matches) {
      sourceRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  const { summary } = fitMap;

  return (
    <div className="mx-auto max-w-6xl px-6 pb-20">
      <section aria-label="Summary" className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Supported" value={summary.supported} tone="text-covered-ink" />
        <Stat label="Partial" value={summary.partial} tone="text-partial-ink" />
        <Stat label="No supporting evidence found" value={summary.not_found} tone="text-missing-ink" />
        <Stat label="Must-haves supported" value={`${summary.must_have_supported} of ${summary.must_have_total}`} />
      </section>

      <details className="group mt-5 rounded-[10px] border border-hairline bg-card">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-4 px-5 py-4">
          <span>
            <span className="font-semibold">Use your own job description</span>
            <span className="block text-sm text-muted">
              {usingSample ? `Currently showing the sample job: ${fitMap.job_title}` : "Currently showing your job description."}
            </span>
          </span>
          <span aria-hidden="true" className="text-muted transition group-open:rotate-180">⌄</span>
        </summary>
        <form onSubmit={mapCustomJob} className="border-t border-hairline px-5 py-4">
          <label htmlFor="jd" className="text-sm font-medium">
            Paste a job description. It is matched against the sample resume and write-up, and not stored.
          </label>
          <textarea
            id="jd"
            value={jobText}
            onChange={(e) => setJobText(e.target.value.slice(0, MAX_JD_CHARS))}
            rows={8}
            placeholder={sampleJobText.split("\n").slice(0, 8).join("\n")}
            className="mt-2 w-full rounded-md border border-[#d6d3cb] bg-paper p-3 font-mono text-sm"
          />
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={busy || !jobText.trim()}
              className="rounded-md bg-accent px-4 py-2.5 text-sm font-medium text-white hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-50"
            >
              {busy ? "Matching…" : "Map requirements"}
            </button>
            {!usingSample && (
              <button type="button" onClick={resetToSample} className="rounded-md border border-[#c9c6be] px-4 py-2.5 text-sm font-medium">
                Back to the sample job
              </button>
            )}
            <span className="ml-auto text-xs text-muted">
              {jobText.length.toLocaleString()} / {MAX_JD_CHARS.toLocaleString()} characters
            </span>
          </div>
          <p role="status" aria-live="polite" className="mt-3 text-sm">
            {error && <span className="text-partial-ink">{error}</span>}
          </p>
        </form>
      </details>

      {(fitMap.warnings.length > 0 || fitMap.ignored_lines.length > 0) && (
        <section aria-label="Notes about the job description" className="mt-4 rounded-[10px] border border-partial-line bg-[#fffbf0] p-4 text-sm">
          <ul className="list-disc space-y-1 pl-5">
            {fitMap.warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
          {fitMap.ignored_lines.length > 0 && (
            <>
              <p className="mt-2 font-medium">Ignored lines:</p>
              <ul className="mt-1 space-y-1 font-mono text-xs text-ink-2">
                {fitMap.ignored_lines.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </>
          )}
        </section>
      )}

      <div className="mt-6 grid items-start gap-5 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)]">
        <section aria-label="Requirements" className="rounded-[10px] border border-hairline bg-card">
          <h2 className="border-b border-hairline px-5 py-3.5 text-sm font-semibold text-ink-2">
            Requirements · {fitMap.results.length}
          </h2>
          <ul>
            {fitMap.results.map((r) => {
              const active = r.requirement.id === selected?.requirement.id;
              return (
                <li key={r.requirement.id}>
                  <button
                    type="button"
                    aria-pressed={active}
                    onClick={() => select(r.requirement.id)}
                    className={`flex w-full flex-wrap items-center gap-3 border-b border-[#f2f0eb] px-5 py-3.5 text-left ${
                      active ? "bg-[#f6f5f1] shadow-[inset_3px_0_0_#16181d]" : "hover:bg-[#fbfbf9]"
                    }`}
                  >
                    <span className="min-w-0 flex-1 basis-60">
                      <span className="block text-[15px]">{r.requirement.text}</span>
                      <span className="text-xs text-muted">
                        {r.requirement.priority === "must" ? "Must-have" : "Nice-to-have"} · asks for{" "}
                        {LEVEL_LABEL[r.requirement.required_level].toLowerCase()}
                      </span>
                    </span>
                    <StatusChip status={r.status} />
                  </button>
                </li>
              );
            })}
          </ul>
        </section>

        <section ref={sourceRef} aria-label="Evidence for the selected requirement" className="scroll-mt-4 space-y-4">
          {selected && (
            <div className="rounded-[10px] border border-hairline bg-card p-5">
              <p className="text-xs text-muted">Selected requirement</p>
              <h2 className="mt-1 text-lg font-semibold">{selected.requirement.text}</h2>
              <div className="mt-3">
                <StatusChip status={selected.status} />
              </div>
              <h3 className="mt-5 text-sm font-semibold text-ink-2">Why</h3>
              <p className="mt-1 text-[15px] leading-relaxed text-ink-2">{selected.reason}</p>
              <h3 className="mt-5 text-sm font-semibold text-ink-2">Cited evidence</h3>
              {citations.length === 0 ? (
                <p className="mt-1 text-[15px] text-muted">None. Nothing in the documents supports this requirement.</p>
              ) : (
                <ul className="mt-2 space-y-3">
                  {citations.map((c) => (
                    <li key={c.evidence_id}>
                      <blockquote className="rounded-md border border-[#efede8] bg-[#fbfbf9] p-3 text-[15px] leading-relaxed">
                        “{c.quote}”
                      </blockquote>
                      <p className="mt-1 font-mono text-xs text-muted">
                        {c.evidence_id} · shows {LEVEL_LABEL[c.level].toLowerCase()}
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          <div ref={docsRef} className="space-y-4">
          {documents.map((doc) => (
            <div key={doc.id} className="rounded-[10px] border border-hairline bg-card p-5">
              <h3 className="text-sm font-semibold text-ink-2">What this parser read: {doc.title}</h3>
              <pre className="relative mt-3 max-h-80 overflow-auto whitespace-pre-wrap rounded-md border border-[#efede8] bg-[#fbfbf9] p-4 font-mono text-[12.5px] leading-relaxed">
                {segmentDocument(
                  doc.text,
                  citations.filter((c) => c.document_id === doc.id),
                ).map((s, i) =>
                  s.evidenceId ? (
                    <mark key={i} className="rounded-sm bg-mark px-0.5 text-ink" title={s.evidenceId}>
                      {s.text}
                    </mark>
                  ) : (
                    <span key={i}>{s.text}</span>
                  ),
                )}
              </pre>
            </div>
          ))}
          </div>
        </section>
      </div>
    </div>
  );
}

function Stat({ label, value, tone = "text-ink" }: { label: string; value: number | string; tone?: string }) {
  return (
    <div className="rounded-[10px] border border-hairline bg-card px-4 py-3.5">
      <p className="text-xs text-muted">{label}</p>
      <p className={`mt-1 text-2xl font-semibold ${tone}`}>{value}</p>
    </div>
  );
}
