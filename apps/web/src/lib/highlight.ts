import type { Citation } from "./types";

export interface Segment {
  text: string;
  /** Evidence id when this segment is a cited quote, otherwise null. */
  evidenceId: string | null;
}

/**
 * Split a document into plain and highlighted segments for the cited spans.
 *
 * Citations come from the API as character offsets, so the highlighted text is
 * always exactly the text the matcher cited. Overlapping spans are merged into the
 * first one; spans outside the document are ignored rather than trusted.
 */
export function segmentDocument(text: string, citations: Citation[]): Segment[] {
  const spans = citations
    .filter((c) => c.start >= 0 && c.end <= text.length && c.start < c.end)
    .filter((c) => text.slice(c.start, c.end) === c.quote)
    .sort((a, b) => a.start - b.start || b.end - a.end);

  const segments: Segment[] = [];
  let cursor = 0;
  for (const span of spans) {
    if (span.start < cursor) continue; // overlaps a span already highlighted
    if (span.start > cursor) segments.push({ text: text.slice(cursor, span.start), evidenceId: null });
    segments.push({ text: text.slice(span.start, span.end), evidenceId: span.evidence_id });
    cursor = span.end;
  }
  if (cursor < text.length) segments.push({ text: text.slice(cursor), evidenceId: null });
  return segments;
}
