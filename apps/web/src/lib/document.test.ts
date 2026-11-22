import { describe, expect, it } from "vitest";

import fitmap from "@/data/sample/fitmap.json";
import { readFileSync } from "node:fs";
import path from "node:path";

import { maskContact, parseDocument, sectionBullets } from "./document";
import type { Citation, FitMap } from "./types";

const cite = (start: number, end: number, quote: string, id = "E1"): Citation => ({
  evidence_id: id,
  document_id: "RES",
  start,
  end,
  quote,
  level: 3,
  score: 1,
});

describe("parseDocument", () => {
  it("drops markdown markers and highlights the cited span in place", () => {
    const text = "# Name\n\n## Experience\n\n- Built a model.\n- Wrote SQL.";
    const start = text.indexOf("Wrote SQL.");
    const blocks = parseDocument(text, [cite(start, start + 10, "Wrote SQL.")]);
    expect(blocks.map((b) => b.kind)).toEqual(["title", "heading", "bullet", "bullet"]);
    expect(blocks[3].pieces).toEqual([{ text: "Wrote SQL.", evidenceId: "E1" }]);
    expect(blocks[2].highlighted).toBe(false);
  });

  it("ignores citations whose quote does not match the offsets", () => {
    const blocks = parseDocument("- Built a model.", [cite(2, 7, "Wrong")]);
    expect(blocks[0].highlighted).toBe(false);
  });

  it("hides contact details on lines without citations", () => {
    expect(maskContact("Edmonton · jo@example.com · +1 780 555 0199")).toBe("Edmonton · [email hidden] · [phone hidden]");
    const blocks = parseDocument("Edmonton · jo@example.com", []);
    expect(blocks[0].pieces[0].text).toContain("[email hidden]");
  });

  it("highlights every citation in the bundled sample", () => {
    const dir = path.join(process.cwd(), "src/data/sample");
    const docs = { RES: readFileSync(path.join(dir, "resume.md"), "utf8"), WRT: readFileSync(path.join(dir, "writeup.md"), "utf8") };
    for (const result of (fitmap as FitMap).results) {
      for (const c of result.citations) {
        const blocks = parseDocument(docs[c.document_id as "RES" | "WRT"], [c]);
        const marked = blocks.flatMap((b) => b.pieces).filter((p) => p.evidenceId === c.evidence_id);
        expect(marked.map((p) => p.text)).toEqual([c.quote]);
      }
    }
  });

  it("lists the bullets of one section", () => {
    const text = "## Experience\n- One\n- Two\n## Education\n- Three";
    expect(sectionBullets(text, "Experience")).toEqual(["One", "Two"]);
  });
});
