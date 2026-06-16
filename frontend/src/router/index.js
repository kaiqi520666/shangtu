// src/router/index.js
import { createRouter, createWebHistory } from "vue-router";
import { getCurrentUser } from "@/api/auth.js";
import { useAuthStore } from "@/stores/auth.js";
import HomeView from "../views/HomeView.vue";

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: "/",
      name: "home",
      component: HomeView,
    },
    {
      path: "/login",
      name: "login",
      component: () => import("../views/auth/LoginView.vue"),
    },
    {
      path: "/register",
      name: "register",
      component: () => import("../views/auth/RegisterView.vue"),
    },
    {
      path: "/generator",
      redirect: "/generator/product-suite",
    },
    {
      path: "/generator/product-suite/:jobId?",
      name: "product-suite",
      component: () => import("../views/generator/product-suite/ProductSuiteView.vue"),
    },
    {
      path: "/generator/product-image/:jobId?",
      name: "product-image",
      component: () => import("../views/generator/product-image/ProductImageView.vue"),
    },
    {
      path: "/generator/outfit/:jobId?",
      name: "outfit",
      component: () => import("../views/generator/outfit/OutfitView.vue"),
    },
    {
      path: "/generator/free-image/:jobId?",
      name: "free-image",
      component: () => import("../views/generator/free-image/FreeImageView.vue"),
    },
    {
      path: "/generator/assets",
      name: "assets",
      component: () => import("../views/generator/assets/AssetLibraryView.vue"),
    },
    {
      path: "/admin",
      name: "admin",
      component: () => import("../views/admin/AdminView.vue"),
    },
  ],
});

let profileSynced = false;

router.beforeEach(async (to) => {
  const authStore = useAuthStore();
  const requiresAuth = to.path.startsWith("/generator") || to.path.startsWith("/admin");
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
