import { ref } from "vue";
import { getAccountProfile } from "@/api/account.js";
import { useAuthStore } from "@/stores/auth.js";
import { useToast } from "@/composables/useToast.js";
import { getApiErrorMessage } from "@/utils/apiError.js";

export function useAccountProfile() {
  const toast = useToast();
  const authStore = useAuthStore();
  const profile = ref(null);
  const loading = ref(false);

  async function loadProfile() {
    loading.value = true;
    try {
      const result = await getAccountProfile();
      if (result.code !== 0) {
        toast.error(result.message || "加载账号信息失败");
        return;
      }
      profile.value = result.data;
      authStore.setAuthUser({
        ...result.data,
        token: authStore.token,
      });
    } catch (error) {
      toast.error(getApiErrorMessage(error, "加载账号信息失败"));
    } finally {
      loading.value = false;
    }
  }

  return {
    profile,
    loading,
    loadProfile,
  };
}
