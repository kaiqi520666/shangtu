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
        path: "image-tasks",
        name: "admin-image-tasks",
        component: () => import("@/views/admin/AdminImageTasksView.vue"),
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
        path: "audit-logs",
        name: "admin-audit-logs",
        component: () => import("@/views/admin/AdminAuditLogsView.vue"),
      },
    ],
  },
];
