// @vitest-environment jsdom
import { mount } from "@vue/test-utils";
import { nextTick } from "vue";
import { describe, expect, it } from "vitest";
import AiAssistedTextarea from "./AiAssistedTextarea.vue";

function deferred() {
  let resolve;
  const promise = new Promise((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

function mountTextarea(generateDraft, modelValue = "原文") {
  return mount(AiAssistedTextarea, {
    props: {
      modelValue,
      label: "提示词",
      generateDraft,
    },
  });
}

describe("AiAssistedTextarea", () => {
  it("previews a complete result without changing the source and confirms edited text", async () => {
    const wrapper = mountTextarea(async ({ onChunk }) => {
      onChunk("AI 草稿");
      return true;
    });

    await wrapper.get('[data-testid="ai-action"]').trigger("click");
    expect(wrapper.get('[data-testid="ai-source"]').element.value).toBe("原文");
    expect(wrapper.get('[data-testid="ai-draft"]').element.value).toBe("AI 草稿");

    await wrapper.get('[data-testid="ai-draft"]').setValue("编辑后的草稿");
    await wrapper.get('[data-testid="ai-confirm"]').trigger("click");
    expect(wrapper.emitted("update:modelValue").at(-1)).toEqual(["编辑后的草稿"]);
    expect(wrapper.find('[data-testid="ai-draft-panel"]').exists()).toBe(false);
  });

  it("cancels a request without changing the source", async () => {
    let signal;
    const pending = deferred();
    const wrapper = mountTextarea(({ signal: nextSignal }) => {
      signal = nextSignal;
      return pending.promise;
    });

    await wrapper.get('[data-testid="ai-action"]').trigger("click");
    await wrapper.get('[title="取消草稿"]').trigger("click");
    expect(signal.aborted).toBe(true);
    expect(wrapper.emitted("update:modelValue")).toBeUndefined();
  });

  it("keeps partial content when generation fails", async () => {
    const wrapper = mountTextarea(async ({ onChunk }) => {
      onChunk("部分草稿");
      return false;
    });

    await wrapper.get('[data-testid="ai-action"]').trigger("click");
    expect(wrapper.get('[data-testid="ai-draft"]').element.value).toBe("部分草稿");
    expect(wrapper.get('[data-testid="ai-confirm"]').attributes("disabled")).toBeUndefined();
  });

  it("appends incremental chunks to the draft", async () => {
    const wrapper = mountTextarea(async ({ onChunk }) => {
      onChunk("第一段");
      onChunk("第二段");
      return true;
    });

    await wrapper.get('[data-testid="ai-action"]').trigger("click");
    expect(wrapper.get('[data-testid="ai-draft"]').element.value).toBe("第一段第二段");
  });

  it("aborts and isolates a late response when retrying", async () => {
    const first = deferred();
    const signals = [];
    let calls = 0;
    const wrapper = mountTextarea(async ({ signal, onChunk }) => {
      signals.push(signal);
      calls += 1;
      if (calls === 1) {
        await first.promise;
        onChunk("过期草稿");
        return true;
      }
      onChunk("新草稿");
      return true;
    });

    await wrapper.get('[data-testid="ai-action"]').trigger("click");
    await wrapper.get('[data-testid="ai-retry"]').trigger("click");
    expect(signals[0].aborted).toBe(true);
    expect(wrapper.get('[data-testid="ai-draft"]').element.value).toBe("新草稿");

    first.resolve();
    await nextTick();
    expect(wrapper.get('[data-testid="ai-draft"]').element.value).toBe("新草稿");
  });

  it("closes stale drafts when the external value changes", async () => {
    const wrapper = mountTextarea(async ({ onChunk }) => {
      onChunk("草稿");
      return true;
    });

    await wrapper.get('[data-testid="ai-action"]').trigger("click");
    await wrapper.setProps({ modelValue: "外部新值" });
    expect(wrapper.find('[data-testid="ai-draft-panel"]').exists()).toBe(false);
  });

  it("aborts an active request on unmount", async () => {
    let signal;
    const pending = deferred();
    const wrapper = mountTextarea(({ signal: nextSignal }) => {
      signal = nextSignal;
      return pending.promise;
    });

    await wrapper.get('[data-testid="ai-action"]').trigger("click");
    wrapper.unmount();
    expect(signal.aborted).toBe(true);
  });
});
