"use client";

import { useId, useState } from "react";

import { hasPlaceholders, splitPlaceholders } from "@/lib/bullets";
import type { Citation } from "@/lib/types";

export interface ApprovedBullet {
  requirement: string;
  text: string;
  token: string;
}

interface Check {
  passed: boolean;
  issues: string[];
  approval_token: string | null;
}

type Source = "model" | "rules";

/**
 * Draft → check → approve, for one requirement.
 *
 * The draft is checked on the server against the cited lines. Approval needs the
 * token for this exact text; any edit clears the check, so an edited bullet must
 * pass again before it can be approved.
 */
export function RewritePanel({
  requirement,
  citations,
  approved,
  onApprove,
}: {
  requirement: string;
  citations: Citation[];
  approved: ApprovedBullet | undefined;
  onApprove: (bullet: ApprovedBullet) => void;
}) {
  const [text, setText] = useState("");
  const [source, setSource] = useState<Source | null>(null);
  const [check, setCheck] = useState<Check | null>(null);
  const [busy, setBusy] = useState<"draft" | "check" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fieldId = useId();
  const evidence = citations.slice(0, 3).map((c) => ({ id: c.evidence_id, text: c.quote }));

  async function call<T>(url: string, body: object): Promise<T> {
    const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const data = await response.json();
    if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Something went wrong. Try again.");
    return data as T;
  }

  async function draft() {
    setBusy("draft");
    setError(null);
    try {
      const data = await call<{ bullet: string; source: Source; check: Check }>("/api/rewrite", { requirement, evidence });
      setText(data.bullet);
      setSource(data.source);
      setCheck(data.check);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Drafting failed.");
    } finally {
      setBusy(null);
    }
  }

  async function recheck() {
    setBusy("check");
    setError(null);
    try {
      setCheck(await call<Check>("/api/rewrite/check", { text, evidence, requirement }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Checking failed.");
    } finally {
      setBusy(null);
    }
  }

  const needsDetails = hasPlaceholders(text);
  const isApproved = approved !== undefined && approved.text === text.trim();

  if (!source) {
    return (
      <div className="flex flex-wrap items-center gap-3 border-t border-line pt-4">
        <button
          type="button"
          onClick={draft}
          disabled={busy !== null}
          className="min-h-11 rounded-xl border border-mint/40 px-4 text-sm font-semibold text-mint-ink hover:bg-mint/10 disabled:opacity-50"
        >
          {busy === "draft" ? "Drafting…" : "Draft a stronger bullet"}
        </button>
        <span className="text-xs text-subtle">Uses only the lines quoted above. Checked before you can approve it.</span>
        {error && <p role="status" className="w-full text-sm text-amber-ink">{error}</p>}
      </div>
    );
  }

  return (
    <div className="space-y-3 border-t border-line pt-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <label htmlFor={fieldId} className="font-mono text-[11px] uppercase tracking-[0.08em] text-subtle">
          Draft bullet
        </label>
        <span className="text-xs text-subtle">
          {source === "model" ? "Drafted by Claude, then checked by rules" : "Rule-based shape (AI drafting is off or unavailable)"}
        </span>
      </div>
      <textarea
        id={fieldId}
        value={text}
        rows={3}
        maxLength={600}
        onChange={(e) => {
          setText(e.target.value);
          setCheck(null); // an edit invalidates the previous check and approval
        }}
        className="w-full rounded-xl border border-line-2 bg-bg-2 p-3.5 text-[14.5px] leading-relaxed text-fg focus:border-mint/60"
      />
      <p className="text-[13px] text-subtle">
        Placeholders to fill with true details:{" "}
        {splitPlaceholders(text)
          .filter((p) => p.placeholder)
          .map((p) => p.text)
          .join(", ") || "none"}
      </p>

      <div role="status" aria-live="polite" className="text-sm">
        {check === null ? (
          <span className="text-muted">Edited. Check it again before approving.</span>
        ) : check.passed && needsDetails ? (
          <span className="text-muted">The claim check passed. Resolve the placeholders and check the edited bullet before approving.</span>
        ) : check.passed ? (
          <span className="text-mint-ink">Passes the claim check: nothing beyond your evidence (verbs, numbers, tools, scope, outcomes or job-posting wording).</span>
        ) : (
          <ul className="list-disc space-y-1 pl-5 text-amber-ink">
            {check.issues.map((i) => (
              <li key={i}>{i}</li>
            ))}
          </ul>
        )}
        {error && <p className="mt-1 text-amber-ink">{error}</p>}
      </div>

      <div className="flex flex-wrap gap-2">
        {check === null && (
          <button type="button" onClick={recheck} disabled={busy !== null || !text.trim()} className="min-h-11 rounded-xl border border-line-2 px-4 text-sm font-medium hover:bg-panel-2 disabled:opacity-50">
            {busy === "check" ? "Checking…" : "Check again"}
          </button>
        )}
        <button
          type="button"
          disabled={!check?.passed || !check.approval_token || needsDetails || isApproved}
          onClick={() => check?.approval_token && onApprove({ requirement, text: text.trim(), token: check.approval_token })}
          className="min-h-11 rounded-xl bg-mint px-4 text-sm font-semibold text-mint-deep hover:bg-mint-ink disabled:cursor-not-allowed disabled:opacity-40"
        >
          {isApproved ? "Approved" : "Approve"}
        </button>
        <button type="button" onClick={draft} disabled={busy !== null} className="min-h-11 rounded-xl px-3 text-sm text-muted hover:text-fg disabled:opacity-50">
          {busy === "draft" ? "Drafting…" : "Draft again"}
        </button>
      </div>
    </div>
  );
}

/** Approved bullets, ready to copy. Only bullets that passed the check for their exact text appear here. */
export function ApprovedList({ items }: { items: ApprovedBullet[] }) {
  const [copied, setCopied] = useState(false);
  if (items.length === 0) return null;
  return (
    <section aria-label="Approved bullets" className="space-y-3 rounded-2xl border border-mint/30 bg-mint/5 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="font-semibold">Approved bullets · {items.length}</h3>
        <button
          type="button"
          onClick={async () => {
            await navigator.clipboard.writeText(items.map((b) => `- ${b.text}`).join("\n"));
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
          }}
          className="min-h-11 rounded-xl bg-fg px-4 text-sm font-semibold text-bg hover:bg-white"
        >
          {copied ? "Copied" : "Copy all"}
        </button>
      </div>
      <ul className="space-y-2">
        {items.map((b) => (
          <li key={b.requirement} className="rounded-xl bg-bg-2 px-4 py-3 text-[14.5px] leading-relaxed">
            {b.text}
            <span className="mt-1 block text-xs text-subtle">For: {b.requirement}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
