// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import RegisterView from "./RegisterView.vue";

const mocks = vi.hoisted(() => ({
  login: vi.fn(),
  push: vi.fn(),
  register: vi.fn(),
  sendCode: vi.fn(),
  success: vi.fn(),
  error: vi.fn(),
  getCaptchaConfig: vi.fn(),
}));

vi.mock("@/api/auth.js", () => ({
  register: mocks.register,
  sendRegistrationEmailCode: mocks.sendCode,
  getCaptchaConfig: mocks.getCaptchaConfig,
}));
vi.mock("@/stores/auth.js", () => ({ useAuthStore: () => ({ login: mocks.login }) }));
vi.mock("@/composables/useToast.js", () => ({
  useToast: () => ({ success: mocks.success, error: mocks.error }),
}));
vi.mock("vue-router", () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ push: mocks.push }),
}));

describe("RegisterView", () => {
  beforeEach(() => vi.clearAllMocks());

  it("发送验证码并在注册请求中携带验证码", async () => {
    mocks.sendCode.mockResolvedValue({ code: 0, data: { cooldown_seconds: 60 } });
    mocks.getCaptchaConfig.mockResolvedValue({ code: 0, data: { site_key: "site-key" } });
    mocks.register.mockResolvedValue({
      code: 0,
      data: { user_id: 1, username: "user", email: "user@example.com", token: "token" },
    });
    const wrapper = mount(RegisterView, {
      global: {
        stubs: {
          AuthPageShell: { template: "<div><slot /></div>" },
          RouterLink: { template: "<a><slot /></a>" },
          TurnstileWidget: {
            emits: ["verified"],
            template: '<button type="button" data-testid="captcha" @click="$emit(\'verified\', \'captcha-token\')">verify</button>',
          },
        },
      },
    });
    await flushPromises();
    await wrapper.find('input[autocomplete="username"]').setValue("user");
    await wrapper.find('input[type="email"]').setValue("User@Example.com");
    await wrapper.get('[data-testid="captcha"]').trigger("click");
    const sendButton = wrapper.findAll('button[type="button"]').find((button) => button.text() === "发送验证码");
    await sendButton.trigger("click");
    await flushPromises();

    expect(mocks.sendCode).toHaveBeenCalledWith({
      email: "user@example.com",
      captcha_token: "captcha-token",
    });
    expect(sendButton.text()).toBe("60s");

    await wrapper.find('input[autocomplete="one-time-code"]').setValue("123456");
    await wrapper.find('input[type="password"]').setValue("123456");
    await wrapper.find("form").trigger("submit");
    await flushPromises();

    expect(mocks.register).toHaveBeenCalledWith({
      username: "user",
      email: "User@Example.com",
      password: "123456",
      verification_code: "123456",
      invite_code: undefined,
    });
    expect(mocks.login).toHaveBeenCalledOnce();
    expect(mocks.push).toHaveBeenCalledWith("/generator");
    wrapper.unmount();
  });
});
