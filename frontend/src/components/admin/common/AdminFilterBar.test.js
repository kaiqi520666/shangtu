// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import AdminFilterBar from "./AdminFilterBar.vue";

describe("AdminFilterBar", () => {
  it("组合筛选内容、总数和操作按钮", async () => {
    const wrapper = mount(AdminFilterBar, {
      props: { total: 12, totalLabel: "个用户" },
      slots: { default: "<input />", actions: "<button>新增</button>" },
    });

    expect(wrapper.text()).toContain("共 12 个用户");
    expect(wrapper.text()).toContain("新增");
    await wrapper.get("button").trigger("click");
    expect(wrapper.emitted("apply-filter")).toHaveLength(1);
  });
});
