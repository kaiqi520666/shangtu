// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { createMemoryHistory, createRouter } from "vue-router";
import { describe, expect, it } from "vitest";
import AdminLayoutView from "./AdminLayoutView.vue";

const Page = { template: "<div />" };

async function mountLayout(path) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/admin/settings", component: Page },
      { path: "/admin/users", component: Page },
    ],
  });
  await router.push(path);
  await router.isReady();
  const wrapper = mount(AdminLayoutView, {
    global: {
      plugins: [router],
      stubs: { GeneratorLayout: { template: "<div><slot /></div>" } },
    },
  });
  await flushPromises();
  return { router, wrapper };
}

describe("AdminLayoutView", () => {
  it("按当前路由切换一级分组和二级菜单", async () => {
    const { router, wrapper } = await mountLayout("/admin/settings");
    expect(wrapper.get('[aria-label="后台一级导航"]').findAll("a")).toHaveLength(5);
    expect(wrapper.get('[aria-label="后台二级导航"]').text()).toContain("系统配置");
    expect(wrapper.get('[aria-label="后台二级导航"]').text()).toContain("审计日志");

    await router.push("/admin/users");
    await flushPromises();
    const secondary = wrapper.get('[aria-label="后台二级导航"]');
    expect(secondary.findAll("a")).toHaveLength(5);
    expect(secondary.text()).toContain("用户");
    expect(secondary.text()).toContain("提现审核");
    expect(secondary.text()).not.toContain("系统配置");
  });
});
