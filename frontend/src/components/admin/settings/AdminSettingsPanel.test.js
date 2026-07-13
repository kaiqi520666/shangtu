// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import AdminSettingsPanel from "./AdminSettingsPanel.vue";

function createState() {
  return {
    loading: false,
    saving: false,
    imageCreditCosts: { "1K": 1, "2K": 2, "4K": 4 },
    videoCreditCosts: { "720p": 3, "1080p": 5 },
    digitalHumanCreditCosts: { standard: 6, premium: 8 },
    digitalHumanPrechargeCosts: { standard: 100, premium: 200 },
    videoTranslationCreditCosts: { standard: 7, premium: 9 },
    voiceoverCreditCostPer100Chars: 2,
    rechargePackages: [{ id: "p1", name: "套餐", credits: 100, amount_cents: 350, badge: "", enabled: true }],
    paymentConfig: { zpay_pid_configured: true },
  };
}

describe("AdminSettingsPanel", () => {
  it("组合设置分区并透传保存与套餐事件", async () => {
    const state = createState();
    const wrapper = mount(AdminSettingsPanel, { props: { state } });

    expect(wrapper.text()).toContain("生图扣费");
    expect(wrapper.text()).toContain("充值套餐");
    expect(wrapper.text()).toContain("支付配置状态");
    await wrapper.findAll("button").find((button) => button.text() === "新增套餐").trigger("click");
    await wrapper.findAll("button").find((button) => button.text() === "删除").trigger("click");
    await wrapper.findAll("button").find((button) => button.text() === "保存配置").trigger("click");

    expect(wrapper.emitted("add-package")).toHaveLength(1);
    expect(wrapper.emitted("remove-package")[0]).toEqual([0]);
    expect(wrapper.emitted("save")).toHaveLength(1);
  });
});
