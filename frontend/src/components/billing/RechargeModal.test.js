// @vitest-environment jsdom

import { flushPromises, mount, RouterLinkStub } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { beforeEach, describe, expect, it, vi } from "vitest";
import RechargeModal from "./RechargeModal.vue";

const mocks = vi.hoisted(() => ({ getPackages: vi.fn() }));

vi.mock("@/api/billing.js", () => ({
  createBillingOrder: vi.fn(),
  getBillingOrder: vi.fn(),
  getBillingPackages: mocks.getPackages,
  redeemCouponCode: vi.fn(),
}));
vi.mock("@/composables/useToast.js", () => ({
  useToast: () => ({ success: vi.fn(), error: vi.fn() }),
}));

describe("RechargeModal", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    mocks.getPackages.mockResolvedValue({
      code: 0,
      data: {
        packages: [{ id: "p1", credits: 100, amount_cents: 100 }],
        image_credit_costs: {},
        video_credit_costs: {},
        digital_human_credit_costs: {},
        digital_human_precharge_costs: {},
        consumption_multiplier: 1,
      },
    });
  });

  it("loads packages immediately and switches to coupon redemption", async () => {
    const wrapper = mount(RechargeModal, {
      props: { open: true },
      global: { stubs: { RouterLink: RouterLinkStub } },
    });
    await flushPromises();
    expect(mocks.getPackages).toHaveBeenCalledOnce();
    expect(wrapper.text()).toContain("100 积分");
    expect(wrapper.text()).not.toContain("图片按张扣费");
    expect(wrapper.getComponent(RouterLinkStub).props("to")).toBe("/account/pricing");

    const modeButtons = wrapper.findAll("button").filter((button) => button.text() === "优惠码兑换");
    expect(modeButtons).toHaveLength(1);
    await modeButtons[0].trigger("click");
    expect(wrapper.text()).toContain("立即兑换");
  });
});
