// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import AuthForm from "./AuthForm.vue";

describe("AuthForm", () => {
  it("blocks submission while the real request is loading", async () => {
    const wrapper = mount(AuthForm, { props: { mode: "login", loading: true } });
    await wrapper.find('input[type="email"]').setValue("user@example.com");
    await wrapper.find('input[type="password"]').setValue("123456");
    await wrapper.find("form").trigger("submit");
    expect(wrapper.emitted("submit")).toBeUndefined();
  });

  it("emits valid credentials immediately when idle", async () => {
    const wrapper = mount(AuthForm, { props: { mode: "login", loading: false } });
    await wrapper.find('input[type="email"]').setValue("user@example.com");
    await wrapper.find('input[type="password"]').setValue("123456");
    await wrapper.find("form").trigger("submit");
    expect(wrapper.emitted("submit")).toHaveLength(1);
  });
});
