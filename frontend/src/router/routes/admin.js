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
    ],
  },
];
