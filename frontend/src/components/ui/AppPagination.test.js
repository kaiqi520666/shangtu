// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import AppPagination from "./AppPagination.vue";

describe("AppPagination", () => {
  it("只在需要分页时显示并发出方向", async () => {
    const hidden = mount(AppPagination, { props: { state: { page: 1, pageSize: 20, total: 20 } } });
    expect(hidden.find("button").exists()).toBe(false);

    const wrapper = mount(AppPagination, { props: { state: { page: 2, pageSize: 20, total: 60 } } });
    const buttons = wrapper.findAll("button");
    await buttons[0].trigger("click");
    await buttons[1].trigger("click");
    expect(wrapper.emitted("change-page")).toEqual([[-1], [1]]);
  });
});
