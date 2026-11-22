import type { Citation } from "./types";

export type BlockKind = "title" | "heading" | "role" | "bullet" | "para";

export interface Piece {
  text: string;
  /** Evidence id when this piece is a cited quote, otherwise null. */
  evidenceId: string | null;
}

export interface Block {
  kind: BlockKind;
  /** Offset of the first content character (after any "- " or "## " marker). */
  start: number;
  end: number;
  pieces: Piece[];
  highlighted: boolean;
}

// Plain section headings, as they appear in uploaded PDFs and DOCX files.
const PLAIN_HEADING =
  /^(?:(?:work |professional |relevant )?experience|employment(?: history)?|education|skills|technical skills|projects|summary|profile|certifications|publications|awards|volunteering)\s*:?$/i;

export function isPlainHeading(line: string): boolean {
  const t = line.trim();
  return PLAIN_HEADING.test(t) || (/^[A-Z][A-Z &/]{2,40}$/.test(t) && t.split(" ").length <= 4);
}

// Contact details are hidden on screen (ported from the v0.9 privacy_tools module).
const EMAIL = /[\w.+-]+@[\w-]+(?:\.[\w-]+)+/g;
const PHONE = /\+?\d[\d\s().-]{7,}\d/g;

export function maskContact(text: string): string {
  return text.replace(EMAIL, "[email hidden]").replace(PHONE, "[phone hidden]");
}

/** Citations whose offsets really point at their quote. Anything else is not trusted. */
export function validCitations(text: string, citations: Citation[]): Citation[] {
  return citations
    .filter((c) => c.start >= 0 && c.end <= text.length && c.start < c.end)
    .filter((c) => text.slice(c.start, c.end) === c.quote)
    .sort((a, b) => a.start - b.start || b.end - a.end);
}

/**
 * Turn a plain-text document into display blocks with cited spans marked.
 *
 * Highlights come from character offsets, so the marked text is always exactly the
 * text the matcher cited. Markdown markers are dropped from display; a line that
 * holds a citation is never rewritten, so its offsets stay valid.
 */
export function parseDocument(text: string, citations: Citation[]): Block[] {
  const spans = validCitations(text, citations);
  const blocks: Block[] = [];
  let offset = 0;

  for (const line of text.split("\n")) {
    const lineStart = offset;
    const lineEnd = offset + line.length;
    offset = lineEnd + 1;
    if (!line.trim()) continue;

    let kind: BlockKind = "para";
    let prefix = 0;
    if (line.startsWith("# ")) [kind, prefix] = ["title", 2];
    else if (line.startsWith("## ")) [kind, prefix] = ["heading", 3];
    else if (/^[-*] /.test(line)) [kind, prefix] = ["bullet", 2];
    else if (/^\*\*.+\*\*/.test(line)) kind = "role";
    else if (isPlainHeading(line)) kind = "heading";

    const start = lineStart + prefix;
    const pieces: Piece[] = [];
    let cursor = start;
    for (const span of spans) {
      if (span.start < cursor || span.end > lineEnd) continue;
      if (span.start > cursor) pieces.push({ text: text.slice(cursor, span.start), evidenceId: null });
      pieces.push({ text: text.slice(span.start, span.end), evidenceId: span.evidence_id });
      cursor = span.end;
    }
    if (cursor < lineEnd) pieces.push({ text: text.slice(cursor, lineEnd), evidenceId: null });

    const highlighted = pieces.some((p) => p.evidenceId);
    if (!highlighted) {
      for (const piece of pieces) {
        piece.text = maskContact(kind === "role" ? piece.text.replaceAll("**", "") : piece.text);
      }
    }
    blocks.push({ kind, start, end: lineEnd, pieces, highlighted });
  }
  return blocks;
}

/**
 * Bullet lines under one section heading ("## Experience" or a plain "EXPERIENCE").
 * Uploaded resumes without that section fall back to every bullet.
 */
export function sectionBullets(text: string, section: string): string[] {
  const out: string[] = [];
  const all: string[] = [];
  let inSection = false;
  for (const line of text.split("\n")) {
    const heading = line.startsWith("## ") ? line.slice(3) : isPlainHeading(line) ? line : null;
    if (heading !== null) inSection = heading.trim().replace(/:$/, "").toLowerCase().endsWith(section.toLowerCase());
    else if (/^[-*] /.test(line)) {
      all.push(line.slice(2).trim());
      if (inSection) out.push(line.slice(2).trim());
    }
  }
  return out.length > 0 ? out : all;
}
