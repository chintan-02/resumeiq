import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-xl space-y-4 px-6 py-32 text-center">
      <p className="font-mono text-xs uppercase tracking-[0.08em] text-subtle">404</p>
      <h1 className="text-4xl font-semibold tracking-[-0.03em]">This page doesn’t exist</h1>
      <p className="text-muted">The link may be old or mistyped.</p>
      <div className="flex justify-center gap-3 pt-3">
        <Link href="/" className="flex min-h-11 items-center rounded-xl border border-line-2 px-4 font-medium hover:bg-panel">
          Home
        </Link>
        <Link href="/demo" className="flex min-h-11 items-center rounded-xl bg-mint px-4 font-semibold text-mint-deep hover:bg-mint-ink">
          Try the demo
        </Link>
      </div>
    </div>
  );
}
