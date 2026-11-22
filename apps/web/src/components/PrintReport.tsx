import type { ApprovedBullet } from "@/components/RewritePanel";
import { LEVEL_NOUN, STATUS_LABEL, strongestLevel } from "@/lib/labels";
import { privateText } from "@/lib/privacy";
import { KIND_LABEL, PRIORITY_GROUPS } from "@/lib/report";
import type { FitMap } from "@/lib/types";

/**
 * Print-only version of the tailor report (same content as the Markdown export).
 * Hidden on screen; the browser's "Save as PDF" turns it into a PDF.
 */
export function PrintReport({ fitMap, approved, privacy }: { fitMap: FitMap; approved: ApprovedBullet[]; privacy: boolean }) {
  const safe = (t: string) => privateText(t, privacy);
  const s = fitMap.summary;
  return (
    <article aria-hidden="true" className="hidden text-[11pt] leading-snug text-black print:block">
      <header className="border-b border-neutral-300 pb-3">
        <p className="text-[9pt] uppercase tracking-wider text-neutral-500">ResumeIQ · Tailor plan</p>
        <h1 className="mt-1 text-[18pt] font-semibold">{safe(fitMap.job_title)}</h1>
        <p className="mt-1 text-[9.5pt] text-neutral-600">
          Must-haves backed: {s.must_have_supported} of {s.must_have_total} · Backed {s.supported} · Partly backed {s.partial} · No
          evidence found {s.not_found}
          {privacy ? " · Privacy mode on" : ""}
        </p>
      </header>

      {PRIORITY_GROUPS.map((g) => {
        const actions = fitMap.actions.filter((a) => a.priority === g.priority);
        if (actions.length === 0) return null;
        return (
          <section key={g.priority} className="mt-5">
            <h2 className="text-[12.5pt] font-semibold">{g.title}</h2>
            <ol className="mt-2 list-decimal space-y-3 pl-5">
              {actions.map((a) => (
                <li key={a.id} className="break-inside-avoid">
                  <p className="font-medium">
                    {safe(a.title)} <span className="text-[9pt] font-normal text-neutral-500">({KIND_LABEL[a.kind]})</span>
                  </p>
                  <p className="text-neutral-700">{safe(a.detail)}</p>
                  {a.citations.map((c) => (
                    <p key={c.evidence_id} className="mt-1 border-l-2 border-neutral-300 pl-2 text-[10pt] italic text-neutral-600">
                      “{safe(c.quote)}”
                    </p>
                  ))}
                  {a.suggestion && <p className="mt-1 font-mono text-[9.5pt]">{safe(a.suggestion)}</p>}
                </li>
              ))}
            </ol>
          </section>
        );
      })}

      {approved.length > 0 && (
        <section className="mt-5 break-inside-avoid">
          <h2 className="text-[12.5pt] font-semibold">Approved bullets</h2>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {approved.map((b) => (
              <li key={b.requirement}>{safe(b.text)}</li>
            ))}
          </ul>
        </section>
      )}

      <section className="mt-5">
        <h2 className="text-[12.5pt] font-semibold">Requirements</h2>
        <table className="mt-2 w-full border-collapse text-[9.5pt]">
          <thead>
            <tr className="border-b border-neutral-400 text-left">
              <th className="py-1 pr-2 font-semibold">Requirement</th>
              <th className="py-1 pr-2 font-semibold">Priority</th>
              <th className="py-1 pr-2 font-semibold">Status</th>
              <th className="py-1 font-semibold">Strongest evidence</th>
            </tr>
          </thead>
          <tbody>
            {fitMap.results.map((r) => {
              const level = strongestLevel(r.citations);
              return (
                <tr key={r.requirement.id} className="break-inside-avoid border-b border-neutral-200 align-top">
                  <td className="py-1 pr-2">{safe(r.requirement.text)}</td>
                  <td className="py-1 pr-2">{r.requirement.priority === "must" ? "Must" : "Nice"}</td>
                  <td className="py-1 pr-2">{STATUS_LABEL[r.status]}</td>
                  <td className="py-1">{r.citations.length ? LEVEL_NOUN[level] : "none"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>

      {fitMap.health.length > 0 && (
        <section className="mt-5 break-inside-avoid">
          <h2 className="text-[12.5pt] font-semibold">Resume check</h2>
          <ul className="mt-2 space-y-1">
            {fitMap.health.map((h) => (
              <li key={h.id}>
                <span className="font-medium">{h.status === "pass" ? "✓" : "!"} {h.label}:</span> {safe(h.detail)}
              </li>
            ))}
          </ul>
        </section>
      )}
      <p className="mt-6 text-[8.5pt] text-neutral-500">
        Decision support only. ResumeIQ does not score or rank people. Fill every placeholder only with things you really did.
      </p>
    </article>
  );
}
