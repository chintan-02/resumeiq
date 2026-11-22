// Mirrors resumeiq_api.models. Keep in sync when the API contract changes.

export type Coverage = "supported" | "partial" | "not_found";
export type Level = 0 | 1 | 2 | 3 | 4;

export interface Requirement {
  id: string;
  text: string;
  priority: "must" | "nice";
  required_level: Level;
}

export interface Citation {
  evidence_id: string;
  document_id: string;
  start: number;
  end: number;
  quote: string;
  level: Level;
  score: number;
}

export interface RequirementResult {
  requirement: Requirement;
  status: Coverage;
  reason: string;
  citations: Citation[];
  candidates: string[];
}

export interface FitMap {
  job_title: string;
  matcher: string;
  results: RequirementResult[];
  summary: {
    supported: number;
    partial: number;
    not_found: number;
    must_have_supported: number;
    must_have_total: number;
  };
  warnings: string[];
  ignored_lines: string[];
}

export interface SourceDocument {
  id: string;
  kind: "resume" | "writeup";
  title: string;
  text: string;
}
