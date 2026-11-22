import type { Metadata } from "next";

import { DemoWorkspace } from "@/components/DemoWorkspace";
import { loadSample } from "@/lib/sample";

export const metadata: Metadata = {
  title: "Sample fit map",
  description:
    "Try ResumeIQ on a synthetic resume: each job requirement is matched to exact quotes, or marked partial or no supporting evidence found.",
  alternates: { canonical: "/demo" },
};

export default function DemoPage() {
  const { documents, jobText, fitMap } = loadSample();
  return (
    <>
      <div className="mx-auto max-w-6xl px-6 pb-6 pt-10">
        <p className="font-mono text-xs uppercase tracking-[0.08em] text-accent">Sample · synthetic data</p>
        <h1 className="mt-3 font-serif text-4xl tracking-tight sm:text-5xl">Sample fit map</h1>
        <p className="mt-2 text-lg font-medium">Jordan Avery (synthetic) · {fitMap.job_title}</p>
        <p className="mt-3 max-w-3xl leading-relaxed text-ink-2">
          A synthetic resume and project write-up, matched requirement by requirement. Matching is rule-based in this
          version: no AI model reads the documents. Select a requirement to see the exact lines behind its status.
        </p>
      </div>
      <DemoWorkspace documents={documents} sampleJobText={jobText} sampleFitMap={fitMap} />
    </>
  );
}
