"use client";

import { useState } from "react";

import { ApprovedList, RewritePanel, type ApprovedBullet } from "@/components/RewritePanel";
import { splitPlaceholders } from "@/lib/bullets";
import { privateText } from "@/lib/privacy";
import { KIND_LABEL, PRIORITY_GROUPS } from "@/lib/report";
import type { Action, ActionKind, FitMap } from "@/lib/types";

const KIND_STYLE: Record<ActionKind, string> = {
  missing: "border border-dashed border-empty text-muted",
  listed_not_shown: "bg-amber/13 text-amber-ink",
  learned_not_used: "bg-amber/13 text-amber-ink",
  below_level: "bg-amber/13 text-amber-ink",
  partial_coverage: "bg-amber/13 text-amber-ink",
  wording: "bg-sky/14 text-sky-ink",
  add_result: "bg-mint/12 text-mint-ink",
};

// Kinds where drafting from the cited lines makes sense. A skills-list line or a
// course is not something to rewrite; the user needs a new, true line instead.
const DRAFTABLE: ActionKind[] = ["below_level", "partial_coverage", "add_result"];

export function TailorPlan({
  fitMap,
  approved,
  onApprove,
  privacy,
}: {
  fitMap: FitMap;
  approved: Record<string, ApprovedBullet>;
  onApprove: (b: ApprovedBullet) => void;
  privacy: boolean;
}) {
  const requirementText = (id: string | null) => fitMap.results.find((r) => r.requirement.id === id)?.requirement.text;

  if (fitMap.actions.length === 0) {
    return (
      <div className="space-y-5">
        <ApprovedList items={Object.values(approved)} />
        <p className="rounded-2xl border border-line bg-panel p-8 text-center text-muted">
          No changes suggested. Every requirement is backed by a line that shows the level asked.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <p className="max-w-3xl text-[15px] leading-relaxed text-muted">
        What to change for this job, most important first. Every step points at the exact line it is about. Suggestions are
        shapes with placeholders: fill them only with things you really did.
      </p>
      <ApprovedList items={Object.values(approved)} />
      {PRIORITY_GROUPS.map((group) => {
        const actions = fitMap.actions.filter((a) => a.priority === group.priority);
        if (actions.length === 0) return null;
        return (
          <section key={group.priority} aria-labelledby={`plan-${group.priority}`} className="space-y-3">
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1 px-0.5">
              <h3 id={`plan-${group.priority}`} className="font-mono text-xs uppercase tracking-[0.08em] text-subtle">
                {group.title} · {actions.length}
              </h3>
              <p className="text-[13px] text-subtle">{group.blurb}</p>
            </div>
            <ol className="space-y-3">
              {actions.map((a) => (
                <ActionCard
                  key={a.id}
                  action={a}
                  requirement={requirementText(a.requirement_id)}
                  approved={a.requirement_id ? approved[requirementText(a.requirement_id) ?? ""] : undefined}
                  onApprove={onApprove}
                  privacy={privacy}
                />
              ))}
            </ol>
          </section>
        );
      })}
    </div>
  );
}

function ActionCard({
  action,
  requirement,
  approved,
  onApprove,
  privacy,
}: {
  action: Action;
  requirement: string | undefined;
  approved: ApprovedBullet | undefined;
  onApprove: (b: ApprovedBullet) => void;
  privacy: boolean;
}) {
  const [drafting, setDrafting] = useState(false);
  const canDraft = requirement !== undefined && action.citations.length > 0 && DRAFTABLE.includes(action.kind);

  return (
    <li className="rounded-2xl border border-line bg-panel p-5 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
        <h4 className="min-w-0 flex-1 text-[15.5px] font-medium leading-snug">{privateText(action.title, privacy)}</h4>
        <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold ${KIND_STYLE[action.kind]}`}>
          {KIND_LABEL[action.kind]}
        </span>
      </div>
      <p className="mt-2 text-[14.5px] leading-relaxed text-fg-2">{action.detail}</p>

      {action.citations.length > 0 && (
        <div className="mt-4 space-y-2">
          {action.citations.map((c) => (
            <blockquote key={c.evidence_id} className="border-l-2 border-line-2 pl-3.5 text-[14px] leading-relaxed text-muted">
              “{privateText(c.quote, privacy)}”
              <span className="ml-2 font-mono text-[11px] text-subtle">{c.document_id === "WRT" ? "Write-up" : "Resume"}</span>
            </blockquote>
          ))}
        </div>
      )}

      {action.suggestion && <Suggestion text={privateText(action.suggestion, privacy)} />}

      {canDraft && !drafting && (
        <button
          type="button"
          onClick={() => setDrafting(true)}
          className="mt-4 min-h-11 rounded-xl border border-line-2 px-4 text-sm font-medium hover:bg-panel-2"
        >
          Draft a bullet with checks
        </button>
      )}
      {canDraft && drafting && (
        <div className="mt-4">
          <RewritePanel requirement={requirement} citations={action.citations} approved={approved} onApprove={onApprove} />
        </div>
      )}
    </li>
  );
}

function Suggestion({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="mt-4 space-y-2">
      <p className="font-mono text-[11px] uppercase tracking-[0.08em] text-subtle">Shape to fill truthfully</p>
      <div className="flex flex-wrap items-start gap-3 rounded-xl bg-bg-2 px-4 py-3">
        <p className="min-w-0 flex-1 text-[14.5px] leading-relaxed">
          {splitPlaceholders(text).map((part, i) =>
            part.placeholder ? (
              <span key={i} className="text-mint-ink">
                {part.text}
              </span>
            ) : (
              <span key={i}>{part.text}</span>
            ),
          )}
        </p>
        <button
          type="button"
          onClick={async () => {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
          }}
          className="min-h-9 shrink-0 rounded-lg px-2.5 text-xs font-medium text-muted hover:bg-panel-2 hover:text-fg"
        >
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
    </div>
  );
}
