import type { NextConfig } from "next";

// Static CSP: these pages are prerendered, and a nonce-based CSP would force dynamic
// rendering (see the build blueprint). 'unsafe-inline' for scripts is the trade-off
// Next.js needs for hydration without nonces; there is no third-party script on the site.
const csp = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline'",
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data:",
  "font-src 'self'",
  "connect-src 'self'",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
  "object-src 'none'",
].join("; ");

const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=(), interest-cohort=()" },
  ...(process.env.NODE_ENV === "production" ? [{ key: "Content-Security-Policy", value: csp }] : []),
];

const nextConfig: NextConfig = {
  poweredByHeader: false,
  async headers() {
    const headers = [{ source: "/:path*", headers: securityHeaders }];
    // Preview deployments must never be indexed.
    if (process.env.VERCEL_ENV && process.env.VERCEL_ENV !== "production") {
      headers.push({ source: "/:path*", headers: [{ key: "X-Robots-Tag", value: "noindex" }] });
    }
    return headers;
  },
};

export default nextConfig;
