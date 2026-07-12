import { beforeEach, describe, expect, it, vi } from "vitest";
import { createPinia, setActivePinia } from "pinia";

const mocks = vi.hoisted(() => ({
  resetPassword: vi.fn(),
  replace: vi.fn(),
  success: vi.fn(),
  error: vi.fn(),
}));

vi.mock("@/api/admin.js", () => ({ resetAdminUserPassword: mocks.resetPassword }));
vi.mock("vue-router", () => ({ useRouter: () => ({ replace: mocks.replace }) }));
vi.mock("@/composables/useToast.js", () => ({
  useToast: () => ({ success: mocks.success, error: mocks.error }),
}));

import { useAdminPasswordReset } from "./useAdminPasswordReset.js";
import { useAuthStore } from "@/stores/auth.js";

describe("useAdminPasswordReset", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    mocks.resetPassword.mockResolvedValue({ code: 0 });
  });

  it("keeps the admin logged in after resetting another user", async () => {
    const authStore = useAuthStore();
    authStore.login({ userId: 1, email: "admin@example.com", token: "token" });
    const loadUsers = vi.fn();
    const reset = useAdminPasswordReset(loadUsers);
    reset.show({ id: 2, email: "user@example.com" });

    await reset.submit({ newPassword: "new-password", confirmPassword: "new-password" });

    expect(authStore.isAuthenticated).toBe(true);
    expect(loadUsers).toHaveBeenCalledOnce();
    expect(mocks.success).toHaveBeenCalledWith("密码已重置，目标用户需要重新登录");
  });

  it("logs out the admin after resetting their own password", async () => {
    const authStore = useAuthStore();
    authStore.login({ userId: 1, email: "admin@example.com", token: "token" });
    const reset = useAdminPasswordReset(vi.fn());
    reset.show({ id: 1, email: "admin@example.com" });

    await reset.submit({ newPassword: "new-password", confirmPassword: "new-password" });

    expect(authStore.isAuthenticated).toBe(false);
    expect(mocks.replace).toHaveBeenCalledWith({ path: "/login", query: { passwordChanged: "1" } });
  });
});
