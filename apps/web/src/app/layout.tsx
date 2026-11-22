import type { Metadata } from "next";
import Link from "next/link";

import { Logo } from "@/components/Logo";
import { GITHUB_URL, REPORT_URL, SITE_URL } from "@/lib/site";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: "ResumeIQ · Evidence-grounded application copilot", template: "%s · ResumeIQ" },
  description:
    "Map every job requirement to exact quotes from your own resume. Supported, partial or no evidence found, with the source line for each.",
  alternates: { canonical: "/" },
  openGraph: { type: "website", siteName: "ResumeIQ", url: "/" },
  twitter: { card: "summary" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-paper font-sans text-ink antialiased">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-ink focus:px-3 focus:py-2 focus:text-white"
        >
          Skip to content
        </a>
        <header className="border-b border-hairline bg-paper">
          <nav aria-label="Primary" className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-6 py-4">
            <Link href="/" className="order-1 flex items-center gap-2.5 font-semibold tracking-tight">
              <Logo />
              ResumeIQ
            </Link>
            <div className="order-3 flex w-full flex-wrap gap-5 text-sm text-ink-2 sm:order-2 sm:w-auto sm:flex-1">
              <Link href="/#how" className="hover:text-ink">How it works</Link>
              <Link href="/#evaluation" className="hover:text-ink">Evaluation</Link>
              <a href={GITHUB_URL} className="hover:text-ink">GitHub</a>
            </div>
            <Link href="/demo" className="order-2 ml-auto rounded-md bg-ink px-4 py-2.5 text-sm font-medium text-white hover:bg-black sm:order-3">
              Try the sample
            </Link>
          </nav>
        </header>
        <main id="main">{children}</main>
        <footer className="border-t border-hairline">
          <div className="mx-auto flex max-w-6xl flex-wrap justify-between gap-4 px-6 py-8 text-sm text-muted">
            <span>A portfolio project by Chintan Patel · Educational decision support, not a hiring tool</span>
            <span className="flex gap-5">
              <a href={REPORT_URL} className="hover:text-ink">Evaluation report</a>
              <a href={GITHUB_URL} className="hover:text-ink">Source code</a>
            </span>
          </div>
        </footer>
      </body>
    </html>
  );
}
