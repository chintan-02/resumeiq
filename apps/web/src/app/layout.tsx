import type { Metadata, Viewport } from "next";
import Link from "next/link";

import { Logo } from "@/components/Logo";
import { GITHUB_URL, REPORT_URL, SITE_URL } from "@/lib/site";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: { default: "ResumeIQ · Match every requirement to a line you wrote", template: "%s · ResumeIQ" },
  description:
    "Paste a job description and see the exact line in your resume that proves each requirement, how strong it is, and what is still missing.",
  alternates: { canonical: "/" },
  openGraph: { type: "website", siteName: "ResumeIQ", url: "/" },
  twitter: { card: "summary" },
};

export const viewport: Viewport = { themeColor: "#0a0c10", colorScheme: "dark" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-bg font-sans text-fg antialiased">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-fg focus:px-3 focus:py-2 focus:text-bg"
        >
          Skip to content
        </a>
        <header className="border-b border-line print:hidden">
          <nav aria-label="Primary" className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-8 gap-y-3 px-6 py-4 sm:px-8">
            <Link href="/" className="flex items-center gap-2.5 text-[17px] font-semibold tracking-tight">
              <Logo />
              ResumeIQ
            </Link>
            <div className="order-3 flex w-full flex-wrap gap-6 text-sm text-muted sm:order-2 sm:w-auto sm:flex-1">
              <Link href="/#how" className="hover:text-fg">How it works</Link>
              <Link href="/demo" className="hover:text-fg">Sample</Link>
              <Link href="/#evaluation" className="hover:text-fg">Evaluation</Link>
              <a href={GITHUB_URL} className="hover:text-fg">GitHub</a>
            </div>
            <Link
              href="/demo"
              className="order-2 ml-auto flex min-h-11 items-center rounded-xl bg-fg px-4 text-sm font-semibold text-bg hover:bg-white sm:order-3"
            >
              Try the demo
            </Link>
          </nav>
        </header>
        <main id="main">{children}</main>
        <footer className="border-t border-line print:hidden">
          <div className="mx-auto flex max-w-6xl flex-wrap justify-between gap-4 px-6 py-8 text-sm text-subtle sm:px-8">
            <span>A portfolio project by Chintan Patel · Decision support, not a hiring tool</span>
            <span className="flex gap-6">
              <a href={REPORT_URL} className="hover:text-fg">Evaluation report</a>
              <a href={GITHUB_URL} className="hover:text-fg">Source code</a>
            </span>
          </div>
        </footer>
      </body>
    </html>
  );
}
