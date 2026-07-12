import { ref } from "vue";
import { resetAdminUserPassword } from "@/api/admin.js";
import { useAuthStore } from "@/stores/auth.js";
import { useToast } from "@/composables/useToast.js";
import { getApiErrorMessage } from "@/utils/apiError.js";
import { validateNewPassword } from "@/utils/password.js";

export function useAdminPasswordReset(loadUsers) {
  const toast = useToast();
  const open = ref(false);
  const target = ref(null);
  const saving = ref(false);

  function show(user) {
    target.value = user;
    open.value = true;
  }

  async function submit({ newPassword, confirmPassword }) {
    const message = validateNewPassword(newPassword, confirmPassword);
    if (message) return toast.error(message);
    saving.value = true;
    try {
      const result = await resetAdminUserPassword(target.value.id, { new_password: newPassword });
      if (result.code !== 0) return toast.error(result.message || "重置密码失败");
      open.value = false;
      const authStore = useAuthStore();
      if (Number(target.value.id) === Number(authStore.user?.userId)) {
        authStore.logout();
        const { default: router } = await import("@/router/index.js");
        await router.replace({ path: "/login", query: { passwordChanged: "1" } });
        return;
      }
      toast.success("密码已重置，目标用户需要重新登录");
      await loadUsers();
    } catch (error) {
      toast.error(getApiErrorMessage(error, "重置密码失败"));
    } finally {
      saving.value = false;
    }
  }

  return { open, target, saving, show, submit };
}
