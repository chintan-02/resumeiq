import { describe, expect, it } from "vitest";

import fitmap from "@/data/sample/fitmap.json";

import { skillsByArea, skillsIn } from "./skills";
import type { FitMap } from "./types";

describe("skills", () => {
  it("finds skills with symbols and avoids partial words", () => {
    const labels = skillsIn("C++, CI/CD and Python; reactive programming is not React").map((s) => s.label);
    expect(labels).toEqual(expect.arrayContaining(["C++", "CI/CD", "Python", "React"]));
    expect(skillsIn("reactive").map((s) => s.label)).toEqual([]);
    expect(skillsIn("Remote role").map((s) => s.label)).toEqual([]);
  });

  it("groups the sample job's skills with their best status", () => {
    const groups = skillsByArea(fitmap as FitMap);
    const find = (label: string) => groups.flatMap((g) => g.skills).find((s) => s.label === label);
    expect(find("Docker")?.status).toBe("supported");
    expect(find("Azure")?.status).toBe("partial");
    expect(find("Airflow")?.status).toBe("not_found");
    expect(find("Stakeholder communication")?.status).toBe("supported");
  });
});
