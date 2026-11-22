// Copy the API's walkthrough sample into the web app so the demo works even when
// live matching is unavailable. `--check` fails (for CI) if the copies have drifted.
import { readFileSync, writeFileSync, mkdirSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const source = path.resolve(here, "../../api/src/resumeiq_api/samples/walkthrough");
const target = path.resolve(here, "../src/data/sample");
const files = ["resume.md", "writeup.md", "job.md", "fitmap.json"];
const check = process.argv.includes("--check");

mkdirSync(target, { recursive: true });
const drifted = [];
for (const name of files) {
  const want = readFileSync(path.join(source, name), "utf8");
  const dest = path.join(target, name);
  const have = existsSync(dest) ? readFileSync(dest, "utf8") : null;
  if (have === want) continue;
  if (check) drifted.push(name);
  else writeFileSync(dest, want);
}

if (check && drifted.length) {
  console.error(`Sample data out of sync: ${drifted.join(", ")}. Run: npm run sync-sample`);
  process.exit(1);
}
console.log(check ? "Sample data in sync." : `Synced ${files.length} files to src/data/sample.`);
