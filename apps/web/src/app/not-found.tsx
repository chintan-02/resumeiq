import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-xl px-6 py-28 text-center">
      <p className="font-mono text-xs uppercase tracking-[0.08em] text-muted">404</p>
      <h1 className="mt-3 font-serif text-4xl">This page doesn’t exist</h1>
      <p className="mt-3 text-ink-2">The link may be old or mistyped.</p>
      <div className="mt-6 flex justify-center gap-3">
        <Link href="/" className="rounded-md border border-[#c9c6be] px-4 py-2.5 font-medium">Home</Link>
        <Link href="/demo" className="rounded-md bg-accent px-4 py-2.5 font-medium text-white">Try the sample</Link>
      </div>
    </div>
  );
}
