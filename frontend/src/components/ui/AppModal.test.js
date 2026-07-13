// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import AppModal from "./AppModal.vue";

describe("AppModal", () => {
  it("渲染统一 footer 并保留关闭事件", async () => {
    const wrapper = mount(AppModal, {
      props: { open: true, title: "编辑" },
      slots: { default: "<p>内容</p>", footer: "<button>保存</button>" },
    });

    expect(wrapper.text()).toContain("内容");
    expect(wrapper.text()).toContain("保存");
    await wrapper.findAll("button")[0].trigger("click");
    expect(wrapper.emitted("close")).toHaveLength(1);
  });
});
