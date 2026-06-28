export const generatorRoutes = [
  {
    path: "/generator",
    redirect: "/generator/product-suite",
  },
  {
    path: "/generator/product-suite/:jobId?",
    name: "product-suite",
    component: () => import("@/views/generator/product-suite/ProductSuiteView.vue"),
  },
  {
    path: "/generator/product-image/:jobId?",
    name: "product-image",
    component: () => import("@/views/generator/product-image/ProductImageView.vue"),
  },
  {
    path: "/generator/product-video/:jobId?",
    name: "product-video",
    component: () => import("@/views/generator/product-video/ProductVideoView.vue"),
  },
  {
    path: "/generator/outfit/:jobId?",
    name: "outfit",
    component: () => import("@/views/generator/outfit/OutfitView.vue"),
  },
  {
    path: "/generator/free-image/:jobId?",
    name: "free-image",
    component: () => import("@/views/generator/free-image/FreeImageView.vue"),
  },
  {
    path: "/generator/assets",
    name: "assets",
    component: () => import("@/views/assets/AssetLibraryView.vue"),
  },
];
