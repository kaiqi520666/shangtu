import { computed, ref } from "vue";
import { defineStore } from "pinia";

const STORAGE_KEY = "nodepass_auth_user";

function normalizeUser(payload, currentUser = null) {
  if (!payload) return null;
  const email = payload.email || currentUser?.email || "";
  const username = payload.username || currentUser?.username || email?.split("@")[0] || "";
  const token = payload.token || currentUser?.token || "";
  const userId = payload.userId ?? payload.user_id ?? currentUser?.userId ?? null;
  const credits = Number.isFinite(Number(payload.credits))
    ? Number(payload.credits)
    : Number(currentUser?.credits || 0);
  const role = payload.role || currentUser?.role || "user";
  const status = payload.status || currentUser?.status || "active";
  const consumptionMultiplier = Number(payload.consumption_multiplier ?? currentUser?.consumptionMultiplier ?? 1);
  const distributionLevel = payload.distribution_level ?? currentUser?.distributionLevel ?? null;
  const distributionEnabled = Boolean(payload.distribution_enabled ?? currentUser?.distributionEnabled ?? false);

  return {
    email,
    username,
    token,
    userId,
    credits,
    role,
    status,
    consumptionMultiplier,
    distributionLevel,
    distributionEnabled,
    created_at: payload.created_at || currentUser?.created_at || "",
  };
}

export const useAuthStore = defineStore(
  "auth",
  () => {
    const user = ref(null);

    const token = computed(() => user.value?.token || "");
    const credits = computed(() => Number(user.value?.credits || 0));
    const role = computed(() => user.value?.role || "user");
    const status = computed(() => user.value?.status || "active");
    const isAuthenticated = computed(() => Boolean(token.value));
    const isLoggedIn = computed(() => Boolean(user.value?.email));
    const isSuperAdmin = computed(() => role.value === "super_admin" && status.value === "active");
    const distributionEnabled = computed(() => Boolean(user.value?.distributionEnabled));

    function setAuthUser(payload) {
      user.value = normalizeUser(payload, user.value);
    }

    function login(payload) {
      setAuthUser(payload);
    }

    function logout() {
      user.value = null;
    }

    function updateCredits(value) {
      if (!user.value) return;
      user.value = {
        ...user.value,
        credits: Number(value || 0),
      };
    }

    return {
      user,
      token,
      credits,
      role,
      status,
      isAuthenticated,
      isLoggedIn,
      isSuperAdmin,
      distributionEnabled,
      setAuthUser,
      login,
      logout,
      updateCredits,
    };
  },
  {
    persist: {
      key: STORAGE_KEY,
      serializer: {
        serialize: (state) => JSON.stringify(state.user),
        deserialize: (raw) => ({ user: raw ? JSON.parse(raw) : null }),
      },
    },
  },
);
