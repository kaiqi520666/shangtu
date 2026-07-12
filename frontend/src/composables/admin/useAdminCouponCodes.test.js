import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  create: vi.fn(),
  remove: vi.fn(),
  get: vi.fn(),
  update: vi.fn(),
  success: vi.fn(),
  error: vi.fn(),
}));

vi.mock("@/api/admin.js", () => ({
  createAdminCouponCode: mocks.create,
  deleteAdminCouponCode: mocks.remove,
  getAdminCouponCodes: mocks.get,
  updateAdminCouponCode: mocks.update,
}));
vi.mock("@/composables/useToast.js", () => ({
  useToast: () => ({ success: mocks.success, error: mocks.error }),
}));
vi.mock("@/composables/useConfirm.js", () => ({
  useConfirm: () => ({ open: vi.fn().mockResolvedValue(true) }),
}));

import { useAdminCouponCodes } from "./useAdminCouponCodes.js";

describe("useAdminCouponCodes", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.create.mockResolvedValue({ code: 0 });
    mocks.get.mockResolvedValue({ code: 0, data: { items: [], total: 0 } });
  });

  it("normalizes create payload", async () => {
    const coupons = useAdminCouponCodes();
    coupons.openCreate();
    await coupons.saveCoupon({
      code: " welcome-2026 ",
      credits: "100",
      unlimited: true,
      usageLimit: "",
      enabled: true,
    });

    expect(mocks.create).toHaveBeenCalledWith({
      code: "WELCOME-2026",
      credits: 100,
      usage_limit: null,
      enabled: true,
    });
  });

  it("rejects an invalid usage limit before the API call", async () => {
    const coupons = useAdminCouponCodes();
    coupons.openCreate();
    await coupons.saveCoupon({ code: "VALID-CODE", credits: "100", unlimited: false, usageLimit: "0", enabled: true });

    expect(mocks.create).not.toHaveBeenCalled();
    expect(mocks.error).toHaveBeenCalled();
  });
});
