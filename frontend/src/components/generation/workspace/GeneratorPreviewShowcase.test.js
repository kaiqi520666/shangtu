// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import GeneratorPreviewShowcase from "./GeneratorPreviewShowcase.vue";

describe("GeneratorPreviewShowcase", () => {
  it("renders a representative empty-state image", () => {
    const wrapper = mount(GeneratorPreviewShowcase, {
      props: {
        title: "AI 配音",
        subtitle: "输入文本生成配音",
        slides: [],
        imageUrl: "/voiceover.webp",
        imageAlt: "专业录音麦克风",
      },
    });

    const image = wrapper.get("img");
    expect(image.attributes("src")).toBe("/voiceover.webp");
    expect(image.attributes("alt")).toBe("专业录音麦克风");
    expect(wrapper.text()).toContain("AI 配音");
  });
});
