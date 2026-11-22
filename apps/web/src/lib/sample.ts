import { readFileSync } from "node:fs";
import path from "node:path";

import fitmap from "@/data/sample/fitmap.json";
import type { FitMap, SourceDocument } from "./types";

const dir = path.join(process.cwd(), "src/data/sample");
const read = (name: string) => readFileSync(path.join(dir, name), "utf8");

/** The synthetic walkthrough, read at build time. Server-only. */
export function loadSample(): { documents: SourceDocument[]; jobText: string; fitMap: FitMap } {
  return {
    documents: [
      { id: "RES", kind: "resume", title: "Resume (synthetic)", text: read("resume.md") },
      { id: "WRT", kind: "writeup", title: "Project write-up (synthetic)", text: read("writeup.md") },
    ],
    jobText: read("job.md"),
    fitMap: fitmap as FitMap,
  };
}
