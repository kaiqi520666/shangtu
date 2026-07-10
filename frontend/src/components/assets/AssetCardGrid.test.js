// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import AssetCardGrid from "./AssetCardGrid.vue";

describe("AssetCardGrid", () => {
  it("renders an audio player without treating it as an image preview", async () => {
    const wrapper = mount(AssetCardGrid, {
      props: {
        cards: [{
          id: "audio-1",
          taskId: "audio-1",
          mediaType: "audio",
          resultUrl: "https://example.com/audio.mp3",
          dataUrl: "https://example.com/audio.mp3",
          createdAt: "2026-07-10T00:00:00Z",
          selected: false,
          status: "done",
        }],
      },
    });

    expect(wrapper.find("audio").exists()).toBe(true);
    expect(wrapper.find("img").exists()).toBe(false);
    await wrapper.find("audio").trigger("click");
    expect(wrapper.emitted("zoom-card")).toBeUndefined();
  });
});
