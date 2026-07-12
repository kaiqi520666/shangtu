// src/router/index.js
import { createRouter, createWebHistory } from "vue-router";
import { getCurrentUser } from "@/api/auth.js";
import { useAuthStore } from "@/stores/auth.js";
import { accountRoutes } from "./routes/account.js";
import { adminRoutes } from "./routes/admin.js";
import { generatorRoutes } from "./routes/generator.js";
import { publicRoutes } from "./routes/public.js";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [...publicRoutes, ...generatorRoutes, ...accountRoutes, ...adminRoutes],
});

let profileSynced = false;

router.beforeEach(async (to) => {
  const authStore = useAuthStore();
  const requiresAuth = to.path.startsWith("/generator") || to.path.startsWith("/account") || to.path.startsWith("/admin");
  if (requiresAuth && !authStore.isAuthenticated) {
    return {
      path: "/login",
      query: { redirect: to.fullPath },
    };
  }
  if (requiresAuth && !profileSynced) {
    try {
      const result = await getCurrentUser();
      if (result.code === 0) {
        authStore.setAuthUser({
          ...result.data,
          token: authStore.token,
        });
        profileSynced = true;
      } else {
        authStore.logout();
        return {
          path: "/login",
          query: { redirect: to.fullPath },
        };
      }
    } catch {
      authStore.logout();
      return {
        path: "/login",
        query: { redirect: to.fullPath },
      };
    }
  }
  if (to.path.startsWith("/admin") && !authStore.isSuperAdmin) {
    return "/generator/product-suite";
  }
  if (to.path === "/account/distribution" && !authStore.distributionEnabled) {
    return "/account/profile";
  }
  if (
    (to.path === "/login" || to.path === "/register") &&
    authStore.isAuthenticated &&
    to.query.loggedOut !== "1"
  ) {
    return "/generator";
  }
  return true;
});

export default router;
