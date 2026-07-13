// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import AdminSearchInput from "./AdminSearchInput.vue";

describe("AdminSearchInput", () => {
  it("更新关键词并在回车时搜索", async () => {
    const wrapper = mount(AdminSearchInput, { props: { modelValue: "", placeholder: "搜索用户" } });
    const input = wrapper.get("input");

    await input.setValue("demo");
    await input.trigger("keyup.enter");

    expect(wrapper.emitted("update:modelValue")[0]).toEqual(["demo"]);
    expect(wrapper.emitted("search")).toHaveLength(1);
  });
});
