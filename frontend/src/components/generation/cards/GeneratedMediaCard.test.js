// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import GeneratedMediaCard from "./GeneratedMediaCard.vue";

function mountCard(card) {
  return mount(GeneratedMediaCard, {
    props: { card, label: "商品图", mediaLabel: "图片" },
    slots: { preview: "<img data-test='preview'>" },
  });
}

describe("GeneratedMediaCard", () => {
  it("emits activation and download for completed media", async () => {
    const card = { id: "1", status: "done", dataUrl: "image.png", selected: false };
    const wrapper = mountCard(card);

    await wrapper.get('[role="button"]').trigger("click");
    await wrapper.get('button:not([title])').trigger("click");

    expect(wrapper.emitted("activate")?.[0]).toEqual([card]);
    expect(wrapper.emitted("download")?.[0]).toEqual([card]);
  });

  it("shows the failure reason and disables download", () => {
    const wrapper = mountCard({ id: "2", status: "failed", dataUrl: "", errorMessage: "供应商失败", selected: false });

    expect(wrapper.text()).toContain("原因：供应商失败");
    expect(wrapper.get('button:not([title])').attributes("disabled")).toBeDefined();
  });
});
