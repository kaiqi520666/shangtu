import { storeToRefs } from "pinia";
import { useAuthStore } from "@/stores/auth.js";

export function useAuth() {
  const authStore = useAuthStore();
  const { user, token, credits, isAuthenticated, isLoggedIn } = storeToRefs(authStore);

  return {
    user,
    token,
    credits,
    isAuthenticated,
    isLoggedIn,
    login: authStore.login,
    logout: authStore.logout,
    updateCredits: authStore.updateCredits,
    getToken: authStore.getToken,
  };
}
