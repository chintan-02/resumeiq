const vercelProductionHost = process.env.NEXT_PUBLIC_VERCEL_PROJECT_PRODUCTION_URL;

export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ??
  (vercelProductionHost ? `https://${vercelProductionHost}` : "http://localhost:3000");
export const GITHUB_URL = "https://github.com/chintan-02/resumeiq";
export const REPORT_URL =
  "https://github.com/chintan-02/resumeiq/blob/main/evals/reports/eval_v1/REPORT.md";
