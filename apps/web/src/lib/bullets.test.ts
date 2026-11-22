import { describe, expect, it } from "vitest";

import { checkBullet, splitPlaceholders } from "./bullets";

describe("checkBullet", () => {
  it("flags a weak opening and never upgrades it to a stronger verb", () => {
    const c = checkBullet("Contributed to the deployment of the forecasting service to Azure Container Apps with the platform team.");
    expect(c.verb).toBe("weak");
    expect(c.weakOpening).toBe("Contributed to");
    expect(c.tools).toContain("Azure");
    expect(c.suggestion).toBe(
      "[Your verb] the deployment of the forecasting service to Azure Container Apps with the platform team, [add measurable result].",
    );
    expect(c.suggestion).not.toMatch(/\bled\b/i);
  });

  it("treats a count as scale, not as a result", () => {
    const c = checkBullet("Developed a demand-forecasting model in Python with scikit-learn that predicts weekly produce orders for 14 stores.");
    expect(c.verb).toBe("strong");
    expect(c.hasResult).toBe(false);
    expect(c.hasScale).toBe(true);
  });

  it("accepts a bullet with a verb and a measured result", () => {
    const c = checkBullet("Reduced model training time by 40% by caching features in Redis.");
    expect(c.hasResult).toBe(true);
    expect(c.suggestion).toBeNull();
  });

  it("adds a verb placeholder when the bullet has no action verb", () => {
    expect(checkBullet("Forecasting service for stores.").suggestion).toBe(
      "[Action verb] forecasting service for stores, [add measurable result].",
    );
  });

  it("splits placeholders out for styling", () => {
    expect(splitPlaceholders("[Your verb] it, [add result].")).toEqual([
      { text: "[Your verb]", placeholder: true },
      { text: " it, ", placeholder: false },
      { text: "[add result]", placeholder: true },
      { text: ".", placeholder: false },
    ]);
  });
});
