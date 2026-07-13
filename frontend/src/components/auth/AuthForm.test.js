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

  it("requires a six-digit code for registration", async () => {
    const wrapper = mount(AuthForm, { props: { mode: "register" } });
    await wrapper.find('input[autocomplete="username"]').setValue("user");
    await wrapper.find('input[type="email"]').setValue("user@example.com");
    await wrapper.find('input[type="password"]').setValue("123456");
    await wrapper.find("form").trigger("submit");

    expect(wrapper.emitted("submit")).toBeUndefined();
    expect(wrapper.text()).toContain("请输入 6 位验证码");
  });

  it("emits normalized email and verification code actions", async () => {
    const wrapper = mount(AuthForm, { props: { mode: "register" } });
    await wrapper.find('input[autocomplete="username"]').setValue("user");
    await wrapper.find('input[type="email"]').setValue("User@Example.com");
    await wrapper.find('input[autocomplete="one-time-code"]').setValue("123456");
    await wrapper.find('input[type="password"]').setValue("123456");
    const sendButton = wrapper.findAll('button[type="button"]').find((button) => button.text() === "发送验证码");
    await sendButton.trigger("click");
    await wrapper.find("form").trigger("submit");

    expect(wrapper.emitted("send-code")[0]).toEqual(["user@example.com"]);
    expect(wrapper.emitted("submit")[0][0].verificationCode).toBe("123456");
  });
});
