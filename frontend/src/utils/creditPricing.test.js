import { describe, expect, it } from "vitest";
import { applyConsumptionMultiplier, multiplyCreditCosts } from "./creditPricing.js";

describe("creditPricing", () => {
  it("applies the multiplier and rounds the final cost up", () => {
    expect(applyConsumptionMultiplier(21, 0.95)).toBe(20);
    expect(applyConsumptionMultiplier(7, 1.2)).toBe(9);
  });

  it("can adjust fixed per-task price maps", () => {
    expect(multiplyCreditCosts({ "1K": 1, "2K": 2 }, 0.8, true)).toEqual({ "1K": 1, "2K": 2 });
    expect(multiplyCreditCosts({ "720p": 36 }, 1.2)).toEqual({ "720p": 43.2 });
  });
});
