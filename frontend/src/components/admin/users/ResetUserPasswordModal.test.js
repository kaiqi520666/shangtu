// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import ResetUserPasswordModal from "./ResetUserPasswordModal.vue";

describe("ResetUserPasswordModal", () => {
  it("shows the target and submits both password fields", async () => {
    const wrapper = mount(ResetUserPasswordModal, {
      props: { open: true, target: { id: 2, email: "user@example.com" } },
    });
    const inputs = wrapper.findAll("input");
    await inputs[0].setValue("new-password");
    await inputs[1].setValue("new-password");
    await wrapper.find("form").trigger("submit");

    expect(wrapper.text()).toContain("user@example.com");
    expect(wrapper.emitted("submit")[0][0]).toEqual({
      newPassword: "new-password",
      confirmPassword: "new-password",
    });
  });
});
