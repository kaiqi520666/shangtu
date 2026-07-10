// @vitest-environment jsdom

import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import HeygenTranslationLanguageEditorModal from "./HeygenTranslationLanguageEditorModal.vue";

describe("HeygenTranslationLanguageEditorModal", () => {
  it("uses the shared modal close event and preserves submit payload", async () => {
    const form = { name: "English", display_name_zh: "英语", sort_order: 1, enabled: true };
    const wrapper = mount(HeygenTranslationLanguageEditorModal, {
      props: { open: true, form },
    });

    const buttons = wrapper.findAll("button");
    await buttons[0].trigger("click");
    await buttons.at(-1).trigger("click");

    expect(wrapper.emitted("close")).toHaveLength(1);
    expect(wrapper.emitted("submit")[0][0]).toEqual(form);
  });
});
