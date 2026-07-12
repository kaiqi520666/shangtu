import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

const mocks = vi.hoisted(() => ({
  changePassword: vi.fn(),
  replace: vi.fn(),
  error: vi.fn(),
}));

vi.mock("@/api/account.js", () => ({ changeAccountPassword: mocks.changePassword }));
vi.mock("vue-router", () => ({ useRouter: () => ({ replace: mocks.replace }) }));
vi.mock("@/composables/useToast.js", () => ({
  useToast: () => ({ error: mocks.error }),
}));

import { useChangePassword } from "./useChangePassword.js";
import { useAuthStore } from "@/stores/auth.js";

describe("useChangePassword", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("logs out and redirects after success", async () => {
    const authStore = useAuthStore();
    authStore.login({ email: "user@example.com", token: "token" });
    mocks.changePassword.mockResolvedValue({ code: 0 });

    await useChangePassword().submit({
      currentPassword: "old-password",
      newPassword: "new-password",
      confirmPassword: "new-password",
    });

    expect(authStore.isAuthenticated).toBe(false);
    expect(mocks.replace).toHaveBeenCalledWith({ path: "/login", query: { passwordChanged: "1" } });
  });

  it("keeps login state when the API rejects the change", async () => {
    const authStore = useAuthStore();
    authStore.login({ email: "user@example.com", token: "token" });
    mocks.changePassword.mockResolvedValue({ code: 1, message: "当前密码错误" });

    await useChangePassword().submit({
      currentPassword: "wrong-password",
      newPassword: "new-password",
      confirmPassword: "new-password",
    });

    expect(authStore.isAuthenticated).toBe(true);
    expect(mocks.replace).not.toHaveBeenCalled();
    expect(mocks.error).toHaveBeenCalledWith("当前密码错误");
  });
});
