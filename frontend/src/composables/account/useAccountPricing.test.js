import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({ getPricing: vi.fn(), error: vi.fn() }));

vi.mock("@/api/account.js", () => ({ getAccountPricing: mocks.getPricing }));
vi.mock("@/composables/useToast.js", () => ({
  useToast: () => ({ error: mocks.error }),
}));

import { useAccountPricing } from "./useAccountPricing.js";

describe("useAccountPricing", () => {
  beforeEach(() => vi.clearAllMocks());

  it("applies the current account multiplier to every pricing group", async () => {
    mocks.getPricing.mockResolvedValue({
      code: 0,
      data: {
        image_credit_costs: { "1K": 9 },
        video_credit_costs: { "720p": 36 },
        digital_human_credit_costs: { standard: 7 },
        digital_human_precharge_costs: { standard: 2000 },
        video_translation_credit_costs: { standard: 7 },
        voiceover_credit_cost_per_100_chars: 1,
        consumption_multiplier: 1.2,
      },
    });
    const pricing = useAccountPricing();
    await pricing.loadPricing();

    expect(pricing.adjusted.value).toMatchObject({
      multiplier: 1.2,
      image: { "1K": 11 },
      video: { "720p": 43.2 },
      digitalHuman: { standard: 8.4 },
      digitalHumanPrecharge: { standard: 2400 },
      videoTranslation: { standard: 8.4 },
      voiceover: 2,
    });
  });
});
