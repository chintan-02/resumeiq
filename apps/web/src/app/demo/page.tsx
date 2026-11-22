import type { Metadata } from "next";

import { DemoWorkspace } from "@/components/DemoWorkspace";
import { loadSample } from "@/lib/sample";

export const metadata: Metadata = {
  title: "Demo: requirement-by-requirement fit map",
  description:
    "Try ResumeIQ on a synthetic resume: each job requirement is matched to an exact quote, marked partly backed, or shown with no evidence found.",
  alternates: { canonical: "/demo" },
};

export default function DemoPage() {
  const { documents, fitMap } = loadSample();
  // The sample job title is shown inside the workspace, so the header stays short and stable.
  return (
    <>
      <div className="mx-auto max-w-6xl space-y-3 px-6 pb-8 pt-14 sm:px-8">
        <p className="font-mono text-xs uppercase tracking-[0.08em] text-mint-ink">Demo</p>
        <h1 className="text-4xl font-semibold tracking-[-0.03em] sm:text-5xl">See what your resume proves</h1>
        <p className="max-w-3xl text-[17px] leading-relaxed text-muted">
          Opens on a synthetic sample resume. Paste a job description or upload your own resume to see your fit map.
        </p>
      </div>
      <DemoWorkspace documents={documents} sampleFitMap={fitMap} />
    </>
  );
}
