import { ref } from "vue";
import { useRouter } from "vue-router";
import { changeAccountPassword } from "@/api/account.js";
import { useAuthStore } from "@/stores/auth.js";
import { useToast } from "@/composables/useToast.js";
import { getApiErrorMessage } from "@/utils/apiError.js";
import { validatePasswordChange } from "@/utils/password.js";

export function useChangePassword() {
  const router = useRouter();
  const authStore = useAuthStore();
  const toast = useToast();
  const open = ref(false);
  const saving = ref(false);

  async function submit(payload) {
    const message = validatePasswordChange(payload.currentPassword, payload.newPassword, payload.confirmPassword);
    if (message) return toast.error(message);
    saving.value = true;
    try {
      const result = await changeAccountPassword({
        current_password: payload.currentPassword,
        new_password: payload.newPassword,
      });
      if (result.code !== 0) return toast.error(result.message || "修改密码失败");
      authStore.logout();
      await router.replace({ path: "/login", query: { passwordChanged: "1" } });
    } catch (error) {
      toast.error(getApiErrorMessage(error, "修改密码失败"));
    } finally {
      saving.value = false;
    }
  }

  return { open, saving, submit };
}
