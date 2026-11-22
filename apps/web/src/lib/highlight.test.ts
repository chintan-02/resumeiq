import { describe, expect, it } from "vitest";

import fitmap from "../data/sample/fitmap.json";
import { readFileSync } from "node:fs";
import path from "node:path";
import { segmentDocument } from "./highlight";
import type { Citation, FitMap } from "./types";

const cite = (start: number, end: number, quote: string, id = "E1"): Citation => ({
  evidence_id: id,
  document_id: "D",
  start,
  end,
  quote,
  level: 3,
  score: 1,
});

describe("segmentDocument", () => {
  it("highlights cited spans and keeps the rest", () => {
    const text = "Built an API. Wrote tests.";
    const segments = segmentDocument(text, [cite(14, 26, "Wrote tests.")]);
    expect(segments).toEqual([
      { text: "Built an API. ", evidenceId: null },
      { text: "Wrote tests.", evidenceId: "E1" },
    ]);
    expect(segments.map((s) => s.text).join("")).toBe(text);
  });

  it("ignores citations whose quote does not match the offsets", () => {
    const segments = segmentDocument("Built an API.", [cite(0, 5, "Wrote")]);
    expect(segments).toEqual([{ text: "Built an API.", evidenceId: null }]);
  });

  it("ignores out-of-range and overlapping spans", () => {
    const text = "abcdefghij";
    const segments = segmentDocument(text, [cite(2, 6, "cdef", "A"), cite(4, 8, "efgh", "B"), cite(8, 99, "x", "C")]);
    expect(segments.map((s) => s.evidenceId)).toEqual([null, "A", null]);
    expect(segments.map((s) => s.text).join("")).toBe(text);
  });

  it("every citation in the bundled sample matches its source document exactly", () => {
    const dir = path.join(__dirname, "../data/sample");
    const docs: Record<string, string> = {
      RES: readFileSync(path.join(dir, "resume.md"), "utf8"),
      WRT: readFileSync(path.join(dir, "writeup.md"), "utf8"),
    };
    for (const result of (fitmap as FitMap).results) {
      for (const c of result.citations) {
        expect(docs[c.document_id].slice(c.start, c.end)).toBe(c.quote);
      }
    }
  });
});
