import type { Metadata } from "next";

import { DemoWorkspace } from "@/components/DemoWorkspace";
import { loadSample } from "@/lib/sample";

export const metadata: Metadata = {
  title: "Sample fit map",
  description:
    "Try ResumeIQ on a synthetic resume: each job requirement is matched to an exact quote, marked partly backed, or shown with no evidence found.",
  alternates: { canonical: "/demo" },
};

export default function DemoPage() {
  const { documents, fitMap } = loadSample();
  return (
    <>
      <div className="mx-auto max-w-6xl space-y-3 px-6 pb-8 pt-14 sm:px-8">
        <p className="font-mono text-xs uppercase tracking-[0.08em] text-mint-ink">Sample · synthetic data</p>
        <h1 className="text-4xl font-semibold tracking-[-0.03em] sm:text-5xl">Jordan Avery’s fit map</h1>
        <p className="max-w-3xl text-[17px] leading-relaxed text-muted">
          A synthetic resume and project write-up, checked requirement by requirement against{" "}
          <span className="text-fg-2">{fitMap.job_title}</span>. Matching is rule-based: no AI model reads the documents.
          Open a requirement to see the exact line behind its status.
        </p>
      </div>
      <DemoWorkspace documents={documents} sampleFitMap={fitMap} />
    </>
  );
}
