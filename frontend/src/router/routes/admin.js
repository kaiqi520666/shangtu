export const adminRoutes = [
  {
    path: "/admin",
    name: "admin",
    component: () => import("@/views/admin/AdminLayoutView.vue"),
    redirect: "/admin/overview",
    children: [
      {
        path: "overview",
        name: "admin-overview",
        component: () => import("@/views/admin/AdminOverviewView.vue"),
      },
      {
        path: "users",
        name: "admin-users",
        component: () => import("@/views/admin/AdminUsersView.vue"),
      },
      {
        path: "orders",
        name: "admin-orders",
        component: () => import("@/views/admin/AdminOrdersView.vue"),
      },
      {
        path: "transactions",
        name: "admin-transactions",
        component: () => import("@/views/admin/AdminTransactionsView.vue"),
      },
      {
        path: "commission-withdrawals",
        name: "admin-commission-withdrawals",
        component: () => import("@/views/admin/AdminCommissionWithdrawalsView.vue"),
      },
      {
        path: "image-tasks",
        name: "admin-image-tasks",
        component: () => import("@/views/admin/AdminImageTasksView.vue"),
      },
      {
        path: "assets",
        name: "admin-assets",
        component: () => import("@/views/admin/AdminAssetsView.vue"),
      },
      {
        path: "settings",
        name: "admin-settings",
        component: () => import("@/views/admin/AdminSettingsView.vue"),
      },
      {
        path: "product-catalog",
        name: "admin-product-catalog",
        component: () => import("@/views/admin/AdminProductCatalogView.vue"),
      },
      {
        path: "prompt-templates",
        name: "admin-prompt-templates",
        component: () => import("@/views/admin/AdminPromptTemplatesView.vue"),
      },
      {
        path: "outfit-models",
        name: "admin-outfit-models",
        component: () => import("@/views/admin/AdminOutfitModelsView.vue"),
      },
      {
        path: "heygen-avatars",
        name: "admin-heygen-avatars",
        component: () => import("@/views/admin/AdminHeygenAvatarsView.vue"),
      },
      {
        path: "heygen-voices",
        name: "admin-heygen-voices",
        component: () => import("@/views/admin/AdminHeygenVoicesView.vue"),
      },
      {
        path: "heygen-translation-languages",
        name: "admin-heygen-translation-languages",
        component: () => import("@/views/admin/AdminHeygenTranslationLanguagesView.vue"),
      },
      {
        path: "audit-logs",
        name: "admin-audit-logs",
        component: () => import("@/views/admin/AdminAuditLogsView.vue"),
      },
    ],
  },
];
