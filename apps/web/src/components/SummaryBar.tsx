import { StatusSwatch } from "@/components/StatusChip";
import type { FitMap } from "@/lib/types";

/** Must-haves backed, plus a proportional bar of every requirement's status. */
export function SummaryBar({ summary, total }: { summary: FitMap["summary"]; total: number }) {
  const parts = [
    { key: "supported" as const, n: summary.supported, label: "backed", tone: "bg-mint" },
    { key: "partial" as const, n: summary.partial, label: "partly backed", tone: "bg-amber" },
    { key: "not_found" as const, n: summary.not_found, label: "with no evidence", tone: "border-[1.5px] border-dashed border-empty" },
  ];
  return (
    <div className="rounded-2xl border border-line bg-panel px-6 py-5">
      <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-3">
        <p className="text-[15px] text-muted">
          <span className="mr-1.5 text-2xl font-semibold text-fg">
            {summary.must_have_supported} of {summary.must_have_total}
          </span>
          must-haves backed by evidence
        </p>
        <ul className="flex flex-wrap gap-x-5 gap-y-2 text-[13px] text-muted">
          {parts.map((p) => (
            <li key={p.key} className="flex items-center gap-2">
              <StatusSwatch status={p.key} />
              {p.n} {p.label}
            </li>
          ))}
        </ul>
      </div>
      {total > 0 && (
        <div className="mt-4 flex h-2.5 gap-1" aria-hidden="true">
          {parts
            .filter((p) => p.n > 0)
            .map((p) => (
              <div key={p.key} className={`rounded ${p.tone}`} style={{ flexGrow: p.n }} />
            ))}
        </div>
      )}
    </div>
  );
}
