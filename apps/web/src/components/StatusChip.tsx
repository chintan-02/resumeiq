import { STATUS_CLASS, STATUS_LABEL } from "@/lib/labels";
import type { Coverage } from "@/lib/types";

export function StatusChip({ status }: { status: Coverage }) {
  return (
    <span
      className={`inline-flex shrink-0 items-center rounded-full border px-2.5 py-1 text-xs font-medium ${STATUS_CLASS[status]}`}
    >
      {STATUS_LABEL[status]}
    </span>
  );
}
