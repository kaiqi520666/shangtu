// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import AdminNamedResourceModal from "./AdminNamedResourceModal.vue";

describe("AdminNamedResourceModal", () => {
  it("按业务字段映射资源状态", async () => {
    const wrapper = mount(AdminNamedResourceModal, {
      props: {
        open: true,
        form: { id: "m1", name: "模特", sort_order: 2, active: true },
        title: "编辑模特",
        enabledLabel: "启用模特",
        statusField: "active",
      },
    });

    const inputs = wrapper.findAll("input");
    await inputs[0].setValue("新模特");
    await inputs[1].setValue("5");
    await wrapper.findAll("button").at(-1).trigger("click");

    expect(wrapper.emitted("submit")[0][0]).toEqual({ id: "m1", name: "新模特", sort_order: 5, active: true });
  });
});
