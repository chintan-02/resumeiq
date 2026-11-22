import { privateText } from "@/lib/privacy";
import type { HealthCheck } from "@/lib/types";

/** Resume-wide checklist. Pass or warn only: there is deliberately no overall score. */
export function HealthList({ checks, privacy }: { checks: HealthCheck[]; privacy: boolean }) {
  if (checks.length === 0) return null;
  const warnings = checks.filter((c) => c.status === "warn").length;
  return (
    <section aria-labelledby="health-title" className="rounded-2xl border border-line bg-panel p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 id="health-title" className="font-semibold">
          Resume checklist
        </h3>
        <span className="text-sm text-subtle">
          {warnings === 0 ? "Nothing to fix" : `${warnings} to look at`} · no score, on purpose
        </span>
      </div>
      <ul className="mt-4 divide-y divide-line">
        {checks.map((c) => (
          <li key={c.id} className="flex gap-3 py-3.5">
            <span
              aria-hidden="true"
              className={`mt-0.5 grid size-5 shrink-0 place-items-center rounded-full text-[11px] font-bold ${
                c.status === "pass" ? "bg-mint/15 text-mint-ink" : "bg-amber/15 text-amber-ink"
              }`}
            >
              {c.status === "pass" ? "✓" : "!"}
            </span>
            <div className="min-w-0 space-y-1">
              <p className="text-[15px] font-medium">
                {c.label}
                <span className="sr-only">: {c.status === "pass" ? "looks fine" : "worth a look"}</span>
              </p>
              <p className="text-[14px] leading-relaxed text-muted">{c.detail}</p>
              {c.items.length > 0 && (
                <ul className="mt-1.5 space-y-1">
                  {c.items.slice(0, 6).map((item) => (
                    <li key={item} className="rounded-lg bg-bg-2 px-3 py-1.5 text-[13.5px] text-fg-2">
                      {privateText(item, privacy)}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
