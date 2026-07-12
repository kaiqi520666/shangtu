// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import CouponRedeemPanel from "./CouponRedeemPanel.vue";

const mocks = vi.hoisted(() => ({ redeem: vi.fn(), success: vi.fn(), error: vi.fn() }));

vi.mock("@/api/billing.js", () => ({ redeemCouponCode: mocks.redeem }));
vi.mock("@/composables/useToast.js", () => ({
  useToast: () => ({ success: mocks.success, error: mocks.error }),
}));

describe("CouponRedeemPanel", () => {
  beforeEach(() => vi.clearAllMocks());

  it("normalizes the code and displays credited points", async () => {
    mocks.redeem.mockResolvedValue({
      code: 0,
      data: { code: "WELCOME-2026", credits_added: 120, credits: 500 },
    });
    const wrapper = mount(CouponRedeemPanel);
    await wrapper.find("input").setValue(" welcome-2026 ");
    await wrapper.find("form").trigger("submit");
    await vi.waitFor(() => expect(mocks.redeem).toHaveBeenCalledWith("WELCOME-2026"));

    expect(wrapper.text()).toContain("已到账 120 积分");
    expect(wrapper.text()).toContain("当前余额 500 点");
  });

  it("does not call the API for an invalid code", async () => {
    const wrapper = mount(CouponRedeemPanel);
    await wrapper.find("input").setValue("bad code");
    await wrapper.find("form").trigger("submit");

    expect(mocks.redeem).not.toHaveBeenCalled();
    expect(mocks.error).toHaveBeenCalled();
  });
});
