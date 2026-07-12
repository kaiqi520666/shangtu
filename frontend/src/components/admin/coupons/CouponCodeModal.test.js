// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import CouponCodeModal from "./CouponCodeModal.vue";

describe("CouponCodeModal", () => {
  it("submits a new unlimited coupon", async () => {
    const wrapper = mount(CouponCodeModal, { props: { open: true } });
    const inputs = wrapper.findAll("input");
    await inputs[0].setValue("WELCOME-2026");
    await inputs[1].setValue("100");
    await wrapper.find("form").trigger("submit");

    expect(wrapper.emitted("submit")[0][0]).toMatchObject({
      code: "WELCOME-2026",
      credits: 100,
      unlimited: true,
      enabled: true,
    });
  });

  it("locks the code when editing", () => {
    const wrapper = mount(CouponCodeModal, {
      props: {
        open: true,
        target: { id: "coupon-1", code: "FIXED-CODE", credits: 50, usage_limit: 10, used_count: 2, enabled: true },
      },
    });
    expect(wrapper.find('input[type="text"]').attributes("disabled")).toBeDefined();
    expect(wrapper.find('input[type="number"]').element.value).toBe("50");
  });
});
