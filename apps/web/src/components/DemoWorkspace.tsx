"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { PrintReport } from "@/components/PrintReport";
import { HealthList } from "@/components/ResumeCheck";
import { ResumeDocument } from "@/components/ResumeDocument";
import {
  ApprovedList,
  RewritePanel,
  type ApprovedBullet,
} from "@/components/RewritePanel";
import { StatusChip } from "@/components/StatusChip";
import { SummaryBar } from "@/components/SummaryBar";
import { TailorPlan } from "@/components/TailorPlan";
import {
  checkBullet,
  splitPlaceholders,
  type BulletCheck,
} from "@/lib/bullets";
import { sectionBullets } from "@/lib/document";
import { LEVEL_NOUN, MAX_JD_CHARS, MAX_UPLOAD_BYTES } from "@/lib/labels";
import { privateText } from "@/lib/privacy";
import { buildReport, reportFilename } from "@/lib/report";
import { skillsByArea } from "@/lib/skills";
import type {
  Action,
  FitMap,
  Level,
  RequirementResult,
  SourceDocument,
} from "@/lib/types";

interface Props {
  documents: SourceDocument[];
  sampleFitMap: FitMap;
}

const TABS = [
  { id: "plan", label: "Tailor plan" },
  { id: "fit", label: "Fit map" },
  { id: "skills", label: "Skills by area" },
  { id: "check", label: "Resume check" },
] as const;
type TabId = (typeof TABS)[number]["id"];

export function DemoWorkspace({
  documents: sampleDocuments,
  sampleFitMap,
}: Props) {
  const [fitMap, setFitMap] = useState<FitMap>(sampleFitMap);
  const [documents, setDocuments] = useState<SourceDocument[]>(sampleDocuments);
  const [approved, setApproved] = useState<Record<string, ApprovedBullet>>({});
  const [usingSample, setUsingSample] = useState(true);
  const [tab, setTab] = useState<TabId>("plan");
  const [privacy, setPrivacy] = useState(false);
  const [formOpen, setFormOpen] = useState(false);

  // The landing page links to /demo#paste to open the job description box.
  useEffect(() => {
    const open = () => {
      if (window.location.hash === "#paste") setFormOpen(true);
    };
    open();
    window.addEventListener("hashchange", open);
    return () => window.removeEventListener("hashchange", open);
  }, []);

  function showFitMap(
    next: FitMap,
    sample: boolean,
    docs: SourceDocument[] = sampleDocuments,
  ) {
    setFitMap(next);
    setDocuments(docs);
    setApproved({});
    setUsingSample(sample);
    setTab("plan");
    if (!sample)
      requestAnimationFrame(() =>
        document.getElementById("results")?.scrollIntoView({ block: "start" }),
      );
  }

  const approvedList = Object.values(approved);
  const onApprove = (b: ApprovedBullet) =>
    setApproved((prev) => ({ ...prev, [b.requirement]: b }));

  return (
    <>
      <PrintReport fitMap={fitMap} approved={approvedList} privacy={privacy} />
      <div className="mx-auto max-w-6xl space-y-6 px-6 pb-24 sm:px-8 print:hidden">
        <JobForm
          open={formOpen}
          onToggle={setFormOpen}
          usingSample={usingSample}
          onResult={(f, docs) => showFitMap(f, false, docs ?? sampleDocuments)}
          onReset={() => showFitMap(sampleFitMap, true)}
        />

        <div id="results" className="scroll-mt-6">
          <SummaryBar summary={fitMap.summary} total={fitMap.results.length} />
        </div>

        {(fitMap.warnings.length > 0 || fitMap.ignored_lines.length > 0) && (
          <section
            aria-label="Notes about the job description"
            className="rounded-2xl border border-amber/30 bg-amber/8 px-6 py-4 text-sm text-fg-2"
          >
            <ul className="list-disc space-y-1 pl-5">
              {fitMap.warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
            {fitMap.ignored_lines.length > 0 && (
              <div className="mt-3">
                <p className="font-medium text-fg">Ignored lines</p>
                <ul className="mt-1 space-y-1 font-mono text-xs text-muted">
                  {fitMap.ignored_lines.map((line) => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        )}

        <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-3 border-b border-line">
          <Tabs active={tab} onChange={setTab} />
          <Toolbar
            fitMap={fitMap}
            approved={approvedList}
            privacy={privacy}
            onPrivacy={setPrivacy}
          />
        </div>

        <div
          role="tabpanel"
          id={`panel-${tab}`}
          aria-labelledby={`tab-${tab}`}
          tabIndex={0}
          className="outline-none"
        >
          {tab === "plan" && (
            <TailorPlan
              fitMap={fitMap}
              approved={approved}
              onApprove={onApprove}
              privacy={privacy}
            />
          )}
          {tab === "fit" && (
            <FitMapView
              fitMap={fitMap}
              documents={documents}
              approved={approved}
              onApprove={onApprove}
              privacy={privacy}
            />
          )}
          {tab === "skills" && <SkillsView fitMap={fitMap} />}
          {tab === "check" && (
            <CheckView
              fitMap={fitMap}
              documents={documents}
              approved={approvedList}
              privacy={privacy}
            />
          )}
        </div>
      </div>
    </>
  );
}

function Toolbar({
  fitMap,
  approved,
  privacy,
  onPrivacy,
}: {
  fitMap: FitMap;
  approved: ApprovedBullet[];
  privacy: boolean;
  onPrivacy: (on: boolean) => void;
}) {
  function download() {
    const date = new Date().toISOString().slice(0, 10);
    const md = buildReport({ fitMap, approved, privacy, date });
    const url = URL.createObjectURL(
      new Blob([md], { type: "text/markdown;charset=utf-8" }),
    );
    const link = Object.assign(document.createElement("a"), {
      href: url,
      download: reportFilename(fitMap.job_title, date),
    });
    link.click();
    URL.revokeObjectURL(url);
  }
  const button =
    "min-h-10 rounded-lg px-3 text-sm font-medium text-muted hover:bg-panel-2 hover:text-fg";
  return (
    <div className="flex flex-wrap items-center gap-1 pb-1.5">
      <label className="mr-2 flex min-h-10 cursor-pointer items-center gap-2.5 rounded-lg px-2 text-sm text-muted hover:text-fg">
        <input
          type="checkbox"
          role="switch"
          checked={privacy}
          onChange={(e) => onPrivacy(e.target.checked)}
          className="peer sr-only"
        />
        <span
          aria-hidden="true"
          className="relative h-5 w-9 rounded-full bg-line-2 transition-colors peer-checked:bg-mint peer-focus-visible:outline-2 peer-focus-visible:outline-mint after:absolute after:left-0.5 after:top-0.5 after:size-4 after:rounded-full after:bg-fg after:transition-transform peer-checked:after:translate-x-4"
        />
        Privacy mode
      </label>
      <button type="button" onClick={download} className={button}>
        Download report (.md)
      </button>
      <button type="button" onClick={() => window.print()} className={button}>
        Print / Save as PDF
      </button>
    </div>
  );
}

function Tabs({
  active,
  onChange,
}: {
  active: TabId;
  onChange: (id: TabId) => void;
}) {
  const refs = useRef<(HTMLButtonElement | null)[]>([]);

  function onKeyDown(e: React.KeyboardEvent, index: number) {
    const step = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
    if (!step) return;
    e.preventDefault();
    const next = (index + step + TABS.length) % TABS.length;
    onChange(TABS[next].id);
    refs.current[next]?.focus();
  }

  return (
    <div role="tablist" aria-label="Results" className="flex flex-wrap gap-1">
      {TABS.map((t, i) => {
        const selected = t.id === active;
        return (
          <button
            key={t.id}
            ref={(el) => {
              refs.current[i] = el;
            }}
            id={`tab-${t.id}`}
            type="button"
            role="tab"
            aria-selected={selected}
            aria-controls={`panel-${t.id}`}
            tabIndex={selected ? 0 : -1}
            onClick={() => onChange(t.id)}
            onKeyDown={(e) => onKeyDown(e, i)}
            className={`-mb-px min-h-11 border-b-2 px-4 text-[15px] font-medium transition-colors ${
              selected
                ? "border-mint text-fg"
                : "border-transparent text-subtle hover:text-fg-2"
            }`}
          >
            {t.label}
          </button>
        );
      })}
    </div>
  );
}

function JobForm({
  open,
  onToggle,
  usingSample,
  onResult,
  onReset,
}: {
  open: boolean;
  onToggle: (open: boolean) => void;
  usingSample: boolean;
  onResult: (f: FitMap, documents?: SourceDocument[]) => void;
  onReset: () => void;
}) {
  const [jobText, setJobText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!jobText.trim()) return;
    setBusy(true);
    setError(null);
    try {
      if (file && file.size > MAX_UPLOAD_BYTES)
        throw new Error("Files are limited to 2 MB.");
      const response = file
        ? await fetch("/api/upload", {
            method: "POST",
            body: uploadForm(file, jobText),
          })
        : await fetch("/api/fit-map", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ job_description: jobText }),
          });
      const body = await response.json();
      if (!response.ok)
        throw new Error(body.detail ?? "Matching failed. Try again.");
      if (file)
        onResult(body.fit_map as FitMap, body.documents as SourceDocument[]);
      else onResult(body as FitMap);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Matching failed. Try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section
      id="paste"
      aria-label="Your job description"
      className="scroll-mt-24 rounded-2xl border border-line bg-panel"
    >
      <div className="flex flex-wrap items-center justify-between gap-4 px-6 py-5">
        <div>
          <h2 className="text-lg font-semibold">
            {usingSample
              ? "Try it with your own job description"
              : "Showing your results"}
          </h2>
          <p className="mt-0.5 text-sm text-muted">
            Use the sample resume or upload your own. Files are read in memory
            and never stored.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {!usingSample && (
            <button
              type="button"
              onClick={onReset}
              className="min-h-11 rounded-xl border border-line-2 px-4 text-sm font-medium hover:bg-panel-2"
            >
              Back to the sample job
            </button>
          )}
          <button
            type="button"
            aria-expanded={open}
            aria-controls="jd-form"
            onClick={() => onToggle(!open)}
            className="min-h-11 rounded-xl bg-fg px-4 text-sm font-semibold text-bg hover:bg-white"
          >
            {open ? "Close" : "Paste a job description"}
          </button>
        </div>
      </div>
      {open && (
        <form
          id="jd-form"
          onSubmit={submit}
          className="border-t border-line px-6 py-5"
        >
          <label
            htmlFor="resume-file"
            className="text-sm font-medium text-fg-2"
          >
            Your resume{" "}
            <span className="font-normal text-subtle">
              (optional · PDF, DOCX or TXT · up to 2 MB)
            </span>
          </label>
          <input
            id="resume-file"
            type="file"
            accept=".pdf,.docx,.txt,.md"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="mt-2 mb-1 block w-full text-sm text-muted file:mr-4 file:min-h-11 file:cursor-pointer file:rounded-xl file:border file:border-line-2 file:bg-panel-2 file:px-4 file:text-sm file:font-medium file:text-fg hover:file:bg-panel"
          />
          <p className="mb-5 text-xs text-subtle">
            {file
              ? `Using ${file.name}. Contact details are hidden before matching.`
              : "Leave empty to use the synthetic sample resume."}
          </p>
          <label htmlFor="jd" className="text-sm font-medium text-fg-2">
            Job description
          </label>
          <textarea
            id="jd"
            value={jobText}
            onChange={(e) => setJobText(e.target.value.slice(0, MAX_JD_CHARS))}
            rows={9}
            placeholder="Paste the whole posting. Headings like Requirements or Qualifications help, but are not required."
            className="mt-2 w-full rounded-xl border border-line-2 bg-bg-2 p-4 text-sm leading-relaxed text-fg placeholder:text-subtle focus:border-mint/60"
          />
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={busy || !jobText.trim()}
              className="min-h-11 rounded-xl bg-mint px-5 text-sm font-semibold text-mint-deep hover:bg-mint-ink disabled:cursor-not-allowed disabled:opacity-50"
            >
              {busy ? "Matching…" : "Map requirements"}
            </button>
            <span className="ml-auto text-xs text-subtle">
              {jobText.length.toLocaleString()} /{" "}
              {MAX_JD_CHARS.toLocaleString()} characters
            </span>
          </div>
          <p
            role="status"
            aria-live="polite"
            className="mt-3 text-sm text-amber-ink"
          >
            {error}
          </p>
        </form>
      )}
    </section>
  );
}

function uploadForm(file: File, jobText: string): FormData {
  const form = new FormData();
  form.set("resume", file);
  form.set("job_description", jobText);
  return form;
}

function FitMapView({
  fitMap,
  documents,
  approved,
  onApprove,
  privacy,
}: {
  fitMap: FitMap;
  documents: SourceDocument[];
  approved: Record<string, ApprovedBullet>;
  onApprove: (b: ApprovedBullet) => void;
  privacy: boolean;
}) {
  const [selectedId, setSelectedId] = useState(
    fitMap.results[0]?.requirement.id ?? "",
  );
  const docsRef = useRef<HTMLDivElement>(null);
  const selected =
    fitMap.results.find((r) => r.requirement.id === selectedId) ??
    fitMap.results[0];
  // A skill named only in a skills list (or a course) has no backing citation, but
  // the mention itself is worth seeing: highlight it as weak evidence.
  const mentions = useMemo(() => {
    const out: Record<string, Action> = {};
    for (const a of fitMap.actions) {
      if (
        a.requirement_id &&
        (a.kind === "listed_not_shown" || a.kind === "learned_not_used")
      )
        out[a.requirement_id] = a;
    }
    return out;
  }, [fitMap]);
  const selectedMention = selected
    ? mentions[selected.requirement.id]
    : undefined;
  const citations = useMemo(
    () =>
      selected?.citations.length
        ? selected.citations
        : (selectedMention?.citations ?? []),
    [selected, selectedMention],
  );
  const highlight = selected?.citations.length
    ? selected.status
    : selectedMention
      ? "partial"
      : selected?.status;

  useEffect(
    () => setSelectedId(fitMap.results[0]?.requirement.id ?? ""),
    [fitMap],
  );

  // Scroll the document panel (not the page) so the first highlight is in view.
  useEffect(() => {
    const panel = docsRef.current;
    const mark = panel?.querySelector("mark");
    if (panel && mark)
      panel.scrollTo({ top: Math.max(0, mark.offsetTop - 80) });
  }, [citations]);

  if (fitMap.results.length === 0) {
    return (
      <p className="rounded-2xl border border-dashed border-line-2 p-8 text-center text-muted">
        No requirements to show.
      </p>
    );
  }

  const groups = [
    {
      title: "Must-haves",
      items: fitMap.results.filter((r) => r.requirement.priority === "must"),
    },
    {
      title: "Nice to have",
      items: fitMap.results.filter((r) => r.requirement.priority === "nice"),
    },
  ].filter((g) => g.items.length > 0);

  return (
    <div className="flex flex-wrap items-start gap-6">
      <div className="min-w-0 flex-[999_1_520px] space-y-6">
        {groups.map((g) => (
          <section key={g.title} aria-label={g.title} className="space-y-2.5">
            <h3 className="px-0.5 font-mono text-xs uppercase tracking-[0.08em] text-subtle">
              {g.title}
            </h3>
            {g.items.map((r) => (
              <RequirementRow
                key={r.requirement.id}
                result={r}
                selected={r.requirement.id === selected?.requirement.id}
                onSelect={() => setSelectedId(r.requirement.id)}
                approved={approved[r.requirement.text]}
                onApprove={onApprove}
                mention={mentions[r.requirement.id]}
                privacy={privacy}
              />
            ))}
          </section>
        ))}
      </div>

      <div
        ref={docsRef}
        className="relative min-w-0 flex-[1_1_400px] space-y-5 overflow-auto rounded-2xl bg-paper p-7 sm:p-8 lg:sticky lg:top-6 lg:max-h-[calc(100vh-3rem)]"
      >
        <p className="flex justify-between gap-3 text-xs text-paper-muted">
          <span className="font-mono uppercase tracking-[0.06em]">
            Source documents
          </span>
          <span>
            {privacy
              ? "Name, location and contact hidden"
              : "Contact details hidden"}
          </span>
        </p>
        {documents.map((d, i) => (
          <div
            key={d.id}
            className={i > 0 ? "border-t border-paper-line pt-5" : ""}
          >
            <ResumeDocument
              document={d}
              citations={citations}
              status={highlight}
              privacy={privacy}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

function RequirementRow({
  result,
  selected,
  onSelect,
  approved,
  onApprove,
  mention,
  privacy,
}: {
  result: RequirementResult;
  selected: boolean;
  onSelect: () => void;
  approved: ApprovedBullet | undefined;
  onApprove: (b: ApprovedBullet) => void;
  mention: Action | undefined;
  privacy: boolean;
}) {
  const { requirement, status, citations } = result;
  const listedOnly = status === "not_found" && mention !== undefined;
  const strongest = citations.reduce((max, c) => Math.max(max, c.level), 0);
  const tone =
    status === "not_found"
      ? "border-dashed border-line-2"
      : selected
        ? status === "partial"
          ? "border-amber/50"
          : "border-mint/45"
        : "border-line";

  return (
    <div
      className={`rounded-2xl border bg-panel transition-colors ${tone} ${selected ? "bg-panel-2" : "hover:bg-panel-2"}`}
    >
      <button
        type="button"
        aria-expanded={selected}
        onClick={onSelect}
        className="flex min-h-14 w-full items-center justify-between gap-4 px-5 py-4 text-left"
      >
        <span className="text-[15.5px] leading-snug">{requirement.text}</span>
        {listedOnly ? (
          <span className="inline-flex shrink-0 items-center whitespace-nowrap rounded-full border border-dashed border-amber/60 px-2.5 py-1 text-xs font-semibold text-amber-ink">
            {mention.kind === "listed_not_shown"
              ? "Listed, not shown"
              : "Learned, not used"}
          </span>
        ) : (
          <StatusChip status={status} compact />
        )}
      </button>
      {selected && (
        <div className="space-y-3 px-5 pb-5">
          {listedOnly ? (
            <div className="space-y-2">
              {mention.citations.map((c) => (
                <blockquote
                  key={c.evidence_id}
                  className="border-l-2 border-dashed border-amber/60 pl-3.5 text-[14.5px] leading-relaxed text-fg-2"
                >
                  “{privateText(c.quote, privacy)}”
                </blockquote>
              ))}
              <p className="rounded-xl bg-amber/10 px-3.5 py-2.5 text-sm text-amber-ink">
                {mention.kind === "listed_not_shown"
                  ? "Named in your skills list, but no line shows you using it. "
                  : "You studied this, but no line shows you using it. "}
                The job asks for {LEVEL_NOUN[requirement.required_level]}. See
                the Tailor plan for what to add.
              </p>
            </div>
          ) : citations.length === 0 ? (
            <p className="text-sm text-muted">
              Nothing in the resume or write-up supports this. If you have done
              it, add a line that says so.
            </p>
          ) : (
            citations.map((c) => (
              <figure key={c.evidence_id} className="space-y-1.5">
                <blockquote
                  className={`border-l-2 pl-3.5 text-[14.5px] leading-relaxed text-fg-2 ${c.level >= requirement.required_level ? "border-mint" : "border-amber"}`}
                >
                  “{privateText(c.quote, privacy)}”
                </blockquote>
                <figcaption className="font-mono text-xs text-subtle">
                  {c.document_id === "WRT" ? "Write-up" : "Resume"} · shows{" "}
                  {LEVEL_NOUN[c.level]}
                </figcaption>
              </figure>
            ))
          )}
          {status === "partial" && strongest < requirement.required_level && (
            <p className="rounded-xl bg-amber/10 px-3.5 py-2.5 text-sm text-amber-ink">
              The job asks for {LEVEL_NOUN[requirement.required_level]}. The
              strongest line shows {LEVEL_NOUN[strongest as Level]}. Only claim
              more if it is true.
            </p>
          )}
          <details className="text-xs text-subtle">
            <summary className="cursor-pointer select-none py-1 hover:text-muted">
              How this was decided
            </summary>
            <p className="mt-1 leading-relaxed">{result.reason}</p>
            {result.verification_notes?.map((note) => <p key={note} className="mt-1 leading-relaxed">{note}</p>)}
          </details>
          {citations.length > 0 && (
            <RewritePanel
              key={requirement.id + citations.map((c) => c.evidence_id).join()}
              requirement={requirement.text}
              citations={citations}
              approved={approved}
              onApprove={onApprove}
            />
          )}
        </div>
      )}
    </div>
  );
}

const SKILL_STYLE = {
  supported: "bg-mint/12 text-mint-ink",
  partial: "bg-amber/13 text-amber-ink",
  not_found: "border border-dashed border-empty text-muted",
} as const;

function SkillsView({ fitMap }: { fitMap: FitMap }) {
  const groups = skillsByArea(fitMap);
  if (groups.length === 0) {
    return (
      <p className="rounded-2xl border border-dashed border-line-2 p-8 text-center text-muted">
        No known skills were named in this job description.
      </p>
    );
  }
  return (
    <div className="space-y-5">
      <p className="max-w-2xl text-[15px] text-muted">
        Skills the job names, grouped by area, coloured by the strongest
        evidence for them.
      </p>
      <div className="grid gap-4 [grid-template-columns:repeat(auto-fit,minmax(min(320px,100%),1fr))]">
        {groups.map((g) => (
          <section
            key={g.area}
            className="rounded-2xl border border-line bg-panel p-6"
          >
            <h3 className="text-sm font-medium text-subtle">{g.area}</h3>
            <ul className="mt-3 flex flex-wrap gap-2">
              {g.skills.map((s) => (
                <li
                  key={s.label}
                  className={`rounded-full px-3 py-1.5 text-[13.5px] ${SKILL_STYLE[s.status]}`}
                >
                  {s.label}
                  <span className="sr-only">
                    {" "}
                    (
                    {s.status === "supported"
                      ? "backed"
                      : s.status === "partial"
                        ? "partly backed"
                        : "no evidence"}
                    )
                  </span>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </div>
  );
}

function CheckView({
  fitMap,
  documents,
  approved,
  privacy,
}: {
  fitMap: FitMap;
  documents: SourceDocument[];
  approved: ApprovedBullet[];
  privacy: boolean;
}) {
  const resume = documents.find((d) => d.kind === "resume");
  const checks = resume
    ? sectionBullets(resume.text, "Experience").map(checkBullet)
    : [];
  return (
    <div className="space-y-6">
      <ApprovedList items={approved} />
      <HealthList checks={fitMap.health} privacy={privacy} />
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <p className="max-w-2xl text-[15px] text-muted">
          Each experience bullet checked for an action, a tool and a result.
          Missing parts become placeholders. Nothing is invented for you.
        </p>
        <span className="font-mono text-xs text-subtle">
          Rule-based · no AI
        </span>
      </div>
      <div className="grid gap-4 [grid-template-columns:repeat(auto-fit,minmax(min(440px,100%),1fr))]">
        {checks.map((c) => (
          <BulletCard key={c.text} check={c} privacy={privacy} />
        ))}
      </div>
    </div>
  );
}

function BulletCard({
  check,
  privacy,
}: {
  check: BulletCheck;
  privacy: boolean;
}) {
  const flags: { text: string; tone: "good" | "warn" | "plain" }[] = [
    check.verb === "strong"
      ? { text: "Strong action verb", tone: "good" }
      : check.verb === "weak"
        ? { text: `“${check.weakOpening}” shows taking part`, tone: "warn" }
        : { text: "No action verb", tone: "warn" },
    check.tools.length > 0
      ? { text: `Names ${check.tools.join(", ")}`, tone: "good" }
      : { text: "No tool named", tone: "plain" },
    check.hasResult
      ? { text: "Has a result", tone: "good" }
      : {
          text: check.hasScale ? "Shows scale, no result" : "No result",
          tone: "plain",
        },
  ];
  const tone = {
    good: "bg-mint/12 text-mint-ink",
    warn: "bg-amber/13 text-amber-ink",
    plain: "bg-white/6 text-muted",
  };

  return (
    <article className="flex flex-col gap-4 rounded-2xl border border-line bg-panel p-6">
      <p className="text-[15px] leading-relaxed text-fg-2">
        “{privateText(check.text, privacy)}”
      </p>
      <ul className="flex flex-wrap gap-2 text-[13px]">
        {flags.map((f) => (
          <li
            key={f.text}
            className={`rounded-lg px-2.5 py-1.5 ${tone[f.tone]}`}
          >
            {f.text}
          </li>
        ))}
      </ul>
      {check.suggestion ? (
        <div className="space-y-2">
          <p className="font-mono text-[11px] uppercase tracking-[0.08em] text-subtle">
            Stronger shape
          </p>
          <p className="rounded-xl bg-bg-2 px-4 py-3 text-[14.5px] leading-relaxed">
            {splitPlaceholders(check.suggestion).map((part, i) =>
              part.placeholder ? (
                <span key={i} className="text-mint-ink">
                  {part.text}
                </span>
              ) : (
                <span key={i}>{part.text}</span>
              ),
            )}
          </p>
          {check.verb === "weak" && (
            <p className="text-[13px] text-subtle">
              Only write “led” or “owned” if you did. ResumeIQ will not upgrade
              a claim for you.
            </p>
          )}
        </div>
      ) : (
        <p className="text-sm text-mint-ink">Has all three parts.</p>
      )}
    </article>
  );
}
