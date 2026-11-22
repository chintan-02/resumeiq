import { describe, expect, it } from "vitest";

import { maskLocation, maskName, privateText } from "./privacy";

describe("privacy mode", () => {
  it("hides city and region pairs", () => {
    expect(maskLocation("Edmonton, AB · remote")).toBe("[location hidden] · remote");
    expect(maskLocation("Built in New York, NY")).toBe("Built in [location hidden]");
  });

  it("hides a leading name but not a section heading", () => {
    expect(maskName("Jordan Avery (synthetic sample)")).toBe("[name hidden] (synthetic sample)");
    expect(maskName("Professional Experience")).toBe("Professional Experience");
    expect(maskName("EXPERIENCE")).toBe("EXPERIENCE");
  });

  it("always hides contact details, and location only in privacy mode", () => {
    expect(privateText("a@b.co, Calgary, AB", false)).toBe("[email hidden], Calgary, AB");
    expect(privateText("a@b.co, Calgary, AB", true)).toBe("[email hidden], [location hidden]");
  });
});
