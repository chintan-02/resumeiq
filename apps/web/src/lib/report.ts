import { hasPlaceholders } from "./bullets";
import { LEVEL_NOUN, STATUS_LABEL, strongestLevel } from "./labels";
import { privateText } from "./privacy";
import type { Action, ActionKind, FitMap } from "./types";

export const KIND_LABEL: Record<ActionKind, string> = {
  missing: "Not on resume",
  listed_not_shown: "Listed, not shown",
  learned_not_used: "Learned, not used",
  below_level: "Below the level asked",
  partial_coverage: "Partly shown",
  wording: "Wording",
  add_result: "Add a result",
};

export const PRIORITY_GROUPS: { priority: Action["priority"]; title: string; blurb: string }[] = [
  { priority: 1, title: "Fix first", blurb: "Must-haves with no evidence, thin evidence, or evidence below the level asked." },
  { priority: 2, title: "Then", blurb: "Wording the posting uses and nice-to-haves you can partly show." },
  { priority: 3, title: "Polish", blurb: "Results for lines that already back a must-have, and optional extras." },
];

export interface ReportInput {
  fitMap: FitMap;
  approved: { requirement: string; text: string }[];
  privacy: boolean;
  date: string;
}

/**
 * The exported tailor report, as Markdown. It holds the plan, the requirement
 * statuses, the resume checks and approved bullets, plus only the quoted lines the
 * plan is about. It never includes the full resume.
 */
export function buildReport({ fitMap, approved, privacy, date }: ReportInput): string {
  const s = fitMap.summary;
  const safe = (t: string) => privateText(t, privacy);
  const out: string[] = [
    `# Tailor plan: ${safe(fitMap.job_title)}`,
    "",
    `Made with ResumeIQ on ${date}${privacy ? " · privacy mode on" : ""}. Decision support only: every suggestion must stay true to your experience.`,
    "",
    `**Must-haves backed:** ${s.must_have_supported} of ${s.must_have_total} · **Backed:** ${s.supported} · **Partly backed:** ${s.partial} · **No evidence found:** ${s.not_found}`,
    "",
  ];

  for (const group of PRIORITY_GROUPS) {
    const actions = fitMap.actions.filter((a) => a.priority === group.priority);
    if (actions.length === 0) continue;
    out.push(`## ${group.title}`, "", `_${group.blurb}_`, "");
    actions.forEach((a, i) => {
      out.push(`${i + 1}. **${safe(a.title)}** (${KIND_LABEL[a.kind]})`, `   ${safe(a.detail)}`);
      for (const c of a.citations) out.push(`   > ${safe(c.quote).replace(/\s+/g, " ")}`);
      if (a.suggestion) out.push(`   Shape to fill truthfully: \`${safe(a.suggestion)}\``);
      out.push("");
    });
  }
  if (fitMap.actions.length === 0) out.push("## Plan", "", "No changes suggested for this job.", "");

  const completed = approved.filter((bullet) => !hasPlaceholders(bullet.text));
  if (completed.length > 0) {
    out.push("## Approved bullets", "", "_Each passed the claim check for its exact text._", "");
    for (const b of completed) out.push(`- ${safe(b.text)}`);
    out.push("");
  }

  out.push("## Requirements", "", "| Requirement | Priority | Status | Strongest evidence |", "| --- | --- | --- | --- |");
  for (const r of fitMap.results) {
    const level = strongestLevel(r.citations);
    const cell = (t: string) => safe(t).replaceAll("|", "\\|");
    out.push(
      `| ${cell(r.requirement.text)} | ${r.requirement.priority === "must" ? "Must" : "Nice"} | ${STATUS_LABEL[r.status]} | ${
        r.citations.length ? LEVEL_NOUN[level] : "none"
      } |`,
    );
  }
  out.push("");

  if (fitMap.health.length > 0) {
    out.push("## Resume check", "");
    for (const h of fitMap.health) {
      out.push(`- ${h.status === "pass" ? "✓" : "!"} **${h.label}:** ${safe(h.detail)}`);
      for (const item of h.items) out.push(`  - ${safe(item)}`);
    }
    out.push("");
  }
  return out.join("\n");
}

export function reportFilename(jobTitle: string, date: string): string {
  const slug = jobTitle.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 50) || "job";
  return `resumeiq-tailor-plan-${slug}-${date}.md`;
}
