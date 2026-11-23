import { describe, expect, it } from "vitest";

import { loadSample } from "./sample";
import { buildReport, reportFilename } from "./report";

const { fitMap, documents } = loadSample();
const resume = documents.find((d) => d.kind === "resume")!;

describe("tailor report", () => {
  it("lists every action and every requirement", () => {
    const md = buildReport({ fitMap, approved: [], privacy: false, date: "2026-11-22" });
    for (const a of fitMap.actions) expect(md).toContain(a.title);
    for (const r of fitMap.results) expect(md).toContain(r.requirement.text.replaceAll("|", "\\|"));
    expect(md).toContain("## Fix first");
  });

  it("never contains the full resume or contact details", () => {
    const md = buildReport({ fitMap, approved: [], privacy: false, date: "2026-11-22" });
    const quoted = new Set(fitMap.actions.flatMap((a) => a.citations.map((c) => c.quote)));
    const unquotedLines = resume.text
      .split("\n")
      .map((l) => l.replace(/^[-#*\s]+/, "").trim())
      .filter((l) => l.split(" ").length > 6 && ![...quoted].some((q) => l.includes(q)));
    for (const line of unquotedLines) expect(md).not.toContain(line);
    expect(md).not.toMatch(/@example\.com/);
  });

  it("includes approved bullets and respects privacy mode", () => {
    const md = buildReport({
      fitMap,
      approved: [{ requirement: "x", text: "Deployed a model in Edmonton, AB" }],
      privacy: true,
      date: "2026-11-22",
    });
    expect(md).toContain("## Approved bullets");
    expect(md).toContain("[location hidden]");
    expect(md).toContain("privacy mode on");
  });

  it("makes a safe file name", () => {
    expect(reportFilename("Junior ML Engineer / Data (Remote)", "2026-11-22")).toBe(
      "resumeiq-tailor-plan-junior-ml-engineer-data-remote-2026-11-22.md",
    );
  });
});

it("keeps unfinished drafts out of approved exports", () => {
  const md = buildReport({
    fitMap,
    approved: [{ requirement: "Test", text: "Built a tool, [add measurable result]" }],
    privacy: false,
    date: "2026-11-22",
  });
  expect(md).not.toContain("## Approved bullets");
});
