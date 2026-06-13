// src/router/index.js
import { createRouter, createWebHistory } from "vue-router";
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
      path: "/generator/assets",
      name: "assets",
      component: () => import("../views/generator/assets/AssetLibraryView.vue"),
    },
  ],
});

export default router;
