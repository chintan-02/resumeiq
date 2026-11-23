import { skillsIn } from "./skills";

/**
 * Rule-based bullet check, ported from the v0.9 sentence_quality and
 * rewrite_suggestions modules: Action verb + Task + Tool/Method + Result.
 *
 * It never invents content. Anything missing becomes a visible placeholder the
 * writer must fill with something true.
 */

// Strong opening verbs (v0.9 list, plus verbs common in ML resumes).
const STRONG_VERBS = new Set(
  (
    "built developed engineered automated optimized improved reduced increased deployed implemented " +
    "designed analyzed created trained evaluated integrated streamlined delivered packaged wrote led owned " +
    "launched migrated presented shipped architected scaled cut saved mentored"
  ).split(" "),
);

// Openings that show taking part rather than doing (v0.9 weak phrases, plus "contributed to").
const WEAK_OPENINGS = [
  "responsible for",
  "worked on",
  "helped with",
  "helped",
  "assisted with",
  "assisted",
  "participated in",
  "involved in",
  "contributed to",
  "supported",
  "handled",
];

// A result is a measured change, not just a count ("14 stores" is scale, not impact).
const RESULT_PATTERNS = [
  /\b\d+(?:\.\d+)?\s?%/,
  /\$\s?\d/,
  /\b\d+(?:\.\d+)?x\b/i,
  /\b(?:reduc|increas|improv|cut|sav|grew|grow|rais|lower|boost|shorten|speed)\w*\b[^.]*\b(?:by|from|to)\s+\d/i,
  /\bfrom\s+\d[^.]*\bto\s+\d/i,
];
const SCALE_PATTERN = /\b\d[\d,.]*\+?\s+[a-z]/i;

export type VerbStrength = "strong" | "weak" | "missing";

export interface BulletCheck {
  text: string;
  verb: VerbStrength;
  /** The weak opening phrase, when there is one. */
  weakOpening: string | null;
  tools: string[];
  hasResult: boolean;
  hasScale: boolean;
  /** A rewrite shape with placeholders, or null when the bullet has every part. */
  suggestion: string | null;
}

export function checkBullet(text: string): BulletCheck {
  const bullet = text.trim();
  const lower = bullet.toLowerCase();
  const weak = WEAK_OPENINGS.find((p) => lower === p || lower.startsWith(`${p} `)) ?? null;
  const firstWord = lower.split(/\s+/)[0]?.replace(/[^a-z]/g, "") ?? "";
  const verb: VerbStrength = weak ? "weak" : STRONG_VERBS.has(firstWord) ? "strong" : "missing";
  const tools = skillsIn(bullet).map((s) => s.label);
  const hasResult = RESULT_PATTERNS.some((re) => re.test(bullet));
  const hasScale = !hasResult && SCALE_PATTERN.test(bullet);

  let shape = bullet.replace(/[.\s]+$/, "");
  if (weak) shape = `[Your verb]${shape.slice(weak.length)}`;
  else if (verb === "missing") shape = `[Action verb] ${shape.charAt(0).toLowerCase()}${shape.slice(1)}`;
  if (!hasResult) shape = `${shape}, [add measurable result]`;

  return {
    text: bullet,
    verb,
    weakOpening: weak ? bullet.slice(0, weak.length) : null,
    tools,
    hasResult,
    hasScale,
    suggestion: verb === "strong" && hasResult ? null : `${shape}.`,
  };
}

/** Split a suggestion so placeholders like [add measurable result] can be styled. */
export function splitPlaceholders(text: string): { text: string; placeholder: boolean }[] {
  return text
    .split(/(\[[^\]]+\])/)
    .filter(Boolean)
    .map((part) => ({ text: part, placeholder: /^\[[^\]]+\]$/.test(part) }));
}

/** A draft with bracketed placeholders cannot be an approved resume bullet. */
export function hasPlaceholders(text: string): boolean {
  return splitPlaceholders(text).some((part) => part.placeholder);
}
