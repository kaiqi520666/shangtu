// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import GenerationWorkspaceHeader from "./GenerationWorkspaceHeader.vue";

describe("GenerationWorkspaceHeader", () => {
  it("仅在选中卡片后显示批量操作", async () => {
    const wrapper = mount(GenerationWorkspaceHeader, {
      props: {
        title: "新任务",
        titleBadge: "本次生成",
        hasCards: true,
        selectedCount: 0,
        mediaUnit: "张",
      },
    });

    expect(wrapper.text()).not.toContain("全选");
    expect(wrapper.text()).not.toContain("批量下载");

    await wrapper.setProps({ selectedCount: 2 });
    expect(wrapper.text()).toContain("全选");
    expect(wrapper.text()).toContain("批量下载 (2张)");
  });
});
