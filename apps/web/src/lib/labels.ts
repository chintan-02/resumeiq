import type { Coverage, Level } from "./types";

export const STATUS_LABEL: Record<Coverage, string> = {
  supported: "Supported",
  partial: "Partial",
  not_found: "No supporting evidence found",
};

export const LEVEL_LABEL: Record<Level, string> = {
  0: "No direct involvement",
  1: "Awareness",
  2: "Use",
  3: "Building",
  4: "Ownership",
};

export const STATUS_CLASS: Record<Coverage, string> = {
  supported: "border-covered-line bg-covered-bg text-covered-ink",
  partial: "border-partial-line bg-partial-bg text-partial-ink",
  not_found: "border-missing-line bg-missing-bg text-missing-ink",
};

export const MAX_JD_CHARS = 12_000;
