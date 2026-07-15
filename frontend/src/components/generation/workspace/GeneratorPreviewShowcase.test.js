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
    expect(wrapper.text()).not.toContain("AI 配音");
    expect(wrapper.text()).not.toContain("输入文本生成配音");
  });

  it("保留视频示例的标题和说明", () => {
    const wrapper = mount(GeneratorPreviewShowcase, {
      props: {
        title: "商品视频示例",
        subtitle: "预览不同视频风格",
        mediaType: "video",
        slides: [{ id: "ugc", title: "UGC", subtitle: "种草", posterUrl: "/ugc.webp", videoUrl: "/ugc.mp4" }],
      },
    });

    expect(wrapper.text()).toContain("商品视频示例");
    expect(wrapper.text()).toContain("预览不同视频风格");
  });
});
