import { STATUS_LABEL } from "@/lib/labels";
import type { Coverage } from "@/lib/types";

const STYLE: Record<Coverage, string> = {
  supported: "bg-mint/12 text-mint-ink",
  partial: "bg-amber/13 text-amber-ink",
  not_found: "border border-dashed border-empty text-muted",
};

export function StatusChip({ status, compact = false }: { status: Coverage; compact?: boolean }) {
  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full font-semibold ${
        compact ? "px-2.5 py-1 text-xs" : "px-3 py-1.5 text-[13px]"
      } ${STYLE[status]}`}
    >
      {status === "supported" && (
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M5 12l4 4L19 6" />
        </svg>
      )}
      {STATUS_LABEL[status]}
    </span>
  );
}

/** A small square used in legends and the summary bar. */
export function StatusSwatch({ status }: { status: Coverage }) {
  const style =
    status === "supported" ? "bg-mint" : status === "partial" ? "bg-amber" : "border-[1.5px] border-dashed border-subtle";
  return <span aria-hidden="true" className={`inline-block size-2.5 rounded-[3px] ${style}`} />;
}
