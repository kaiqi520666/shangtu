export const accountRoutes = [
  {
    path: "/account",
    component: () => import("@/views/account/AccountLayoutView.vue"),
    redirect: "/account/profile",
    children: [
      {
        path: "profile",
        name: "account-profile",
        component: () => import("@/views/account/AccountProfileView.vue"),
      },
      {
        path: "credits",
        name: "account-credits",
        component: () => import("@/views/account/AccountCreditsView.vue"),
      },
    ],
  },
];
