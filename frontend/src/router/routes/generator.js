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
    path: "/generator/free-video/:jobId?",
    name: "free-video",
    component: () => import("@/views/generator/free-video/FreeVideoView.vue"),
  },
  {
    path: "/generator/digital-human/:jobId?",
    name: "digital-human",
    component: () => import("@/views/generator/digital-human/DigitalHumanView.vue"),
  },
  {
    path: "/generator/video-translation/:jobId?",
    name: "video-translation",
    component: () => import("@/views/generator/video-translation/VideoTranslationView.vue"),
  },
  {
    path: "/generator/voiceover/:jobId?",
    name: "voiceover",
    component: () => import("@/views/generator/voiceover/VoiceoverView.vue"),
  },
  {
    path: "/generator/assets",
    name: "assets",
    component: () => import("@/views/assets/AssetLibraryView.vue"),
  },
];
