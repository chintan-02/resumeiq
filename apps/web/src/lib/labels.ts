import type { Coverage, Level } from "./types";

/** UI wording for the API's coverage values (supported, partial, not_found). */
export const STATUS_LABEL: Record<Coverage, string> = {
  supported: "Backed",
  partial: "Partly backed",
  not_found: "No evidence found",
};

/** How strong a claim is, as a noun: "shows building", "asks for use". */
export const LEVEL_NOUN: Record<Level, string> = {
  0: "no direct involvement",
  1: "awareness",
  2: "use",
  3: "building",
  4: "ownership",
};

export const STATUS_ORDER: Record<Coverage, number> = { supported: 0, partial: 1, not_found: 2 };

export const MAX_JD_CHARS = 12_000;

export const MAX_UPLOAD_BYTES = 2 * 1024 * 1024;
