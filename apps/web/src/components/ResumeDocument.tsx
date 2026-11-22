import { parseDocument, type Block } from "@/lib/document";
import type { Citation, Coverage, SourceDocument } from "@/lib/types";

const HIGHLIGHT: Record<Coverage, string> = {
  supported: "bg-hl text-hl-ink shadow-[0_0_0_1px_#8fddb8]",
  partial: "bg-hl-partial text-paper-ink shadow-[0_0_0_1px_#e7bf7c]",
  not_found: "",
};

/** A source document drawn as paper, with the cited lines highlighted in place. */
export function ResumeDocument({
  document,
  citations,
  status = "supported",
  privacy = false,
}: {
  document: SourceDocument;
  citations: Citation[];
  status?: Coverage;
  privacy?: boolean;
}) {
  const blocks = parseDocument(
    document.text,
    citations.filter((c) => c.document_id === document.id),
    privacy,
  );
  const bullets: Block[][] = [];
  const out: React.ReactNode[] = [];

  // Group consecutive bullets into one list so the document reads naturally.
  blocks.forEach((block, i) => {
    if (block.kind === "bullet") {
      const last = bullets.at(-1);
      if (last && blocks[i - 1]?.kind === "bullet") last.push(block);
      else {
        bullets.push([block]);
        out.push(<BulletList key={block.start} items={bullets.at(-1)!} status={status} />);
      }
      return;
    }
    out.push(<BlockView key={block.start} block={block} status={status} />);
  });

  return (
    <article aria-label={document.title} className="space-y-3 text-paper-ink">
      {out}
    </article>
  );
}

function Pieces({ block, status }: { block: Block; status: Coverage }) {
  return (
    <>
      {block.pieces.map((p, i) =>
        p.evidenceId ? (
          <mark key={i} data-evidence={p.evidenceId} className={`rounded px-1 py-0.5 ${HIGHLIGHT[status]}`}>
            {p.text}
          </mark>
        ) : (
          <span key={i}>{p.text}</span>
        ),
      )}
    </>
  );
}

function BlockView({ block, status }: { block: Block; status: Coverage }) {
  switch (block.kind) {
    case "title":
      return (
        <h3 className="text-2xl font-bold tracking-tight">
          <Pieces block={block} status={status} />
        </h3>
      );
    case "heading":
      return (
        <h4 className="mt-5 border-b border-paper-line pb-1.5 text-xs font-bold uppercase tracking-[0.08em] text-paper-2">
          <Pieces block={block} status={status} />
        </h4>
      );
    case "role":
      return (
        <p className="text-sm font-semibold">
          <Pieces block={block} status={status} />
        </p>
      );
    default:
      return (
        <p className="text-sm leading-relaxed text-paper-2">
          <Pieces block={block} status={status} />
        </p>
      );
  }
}

function BulletList({ items, status }: { items: Block[]; status: Coverage }) {
  return (
    <ul className="list-disc space-y-2 pl-5 text-sm leading-relaxed text-paper-2 marker:text-paper-muted">
      {items.map((b) => (
        <li key={b.start}>
          <Pieces block={b} status={status} />
        </li>
      ))}
    </ul>
  );
}
