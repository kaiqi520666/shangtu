// @vitest-environment jsdom

import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

const listAssets = vi.hoisted(() => vi.fn());

vi.mock("@/api/assets.js", () => ({ listAssets }));

import AssetPickerModal from "./AssetPickerModal.vue";

describe("AssetPickerModal", () => {
  beforeEach(() => {
    listAssets.mockResolvedValue({
      code: 0,
      data: {
        total: 2,
        items: [
          { task_id: "audio-1", media_type: "audio", result_url: "https://example.com/1.mp3", title: "音频 1" },
          { task_id: "audio-2", media_type: "audio", result_url: "https://example.com/2.mp3", title: "音频 2" },
        ],
      },
    });
  });

  it("keeps playback separate from selection and enforces max count", async () => {
    const wrapper = mount(AssetPickerModal, {
      props: { open: true, mediaType: "audio", maxCount: 1 },
    });
    await flushPromises();

    const cards = wrapper.findAll("article");
    expect(cards).toHaveLength(2);
    await wrapper.find("audio").trigger("click");
    expect(wrapper.text()).toContain("添加 0 个");

    await cards[0].trigger("click");
    expect(wrapper.text()).toContain("添加 1 个");
    await cards[1].trigger("click");
    expect(wrapper.emitted("notify")?.at(-1)).toEqual(["最多选择 1 个音频资产"]);
  });
});
