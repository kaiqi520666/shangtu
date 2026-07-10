// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import GeneratorPanelSection from "./GeneratorPanelSection.vue";

describe("GeneratorPanelSection", () => {
  it("renders the shared header content and slots", () => {
    const wrapper = mount(GeneratorPanelSection, {
      props: {
        title: "参考图片",
        description: "上传或从资产库选择",
        tone: "muted",
        divider: false,
      },
      slots: {
        meta: "<span>已选 1/3</span>",
        actions: "<button>清空</button>",
        default: "<div>内容</div>",
      },
    });

    expect(wrapper.text()).toContain("参考图片");
    expect(wrapper.text()).toContain("上传或从资产库选择");
    expect(wrapper.text()).toContain("已选 1/3");
    expect(wrapper.text()).toContain("清空");
    expect(wrapper.classes()).toContain("bg-slate-50/40");
    expect(wrapper.classes()).not.toContain("border-b");
  });

  it("uses the default white divided style and keeps long text wrappable", () => {
    const wrapper = mount(GeneratorPanelSection, {
      props: { title: "这是一个很长的配置分区标题" },
    });

    expect(wrapper.classes()).toContain("bg-white");
    expect(wrapper.classes()).toContain("border-b");
    expect(wrapper.get("header").classes()).toContain("flex-wrap");
  });
});
