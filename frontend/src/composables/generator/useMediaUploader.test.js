import { effectScope, nextTick, reactive } from "vue";
import { describe, expect, it, vi } from "vitest";
import { useMediaUploader } from "./useMediaUploader.js";

function setup(overrides = {}) {
  const props = reactive({ items: [], maxCount: 2, limitMessage: "数量已满", ...overrides });
  const events = [];
  const emit = (event, value) => {
    events.push([event, value]);
    if (event === "update:items") props.items = value;
  };
  const scope = effectScope();
  const uploader = scope.run(() => useMediaUploader({
    props,
    emit,
    itemsKey: "items",
    updateEvent: "update:items",
    mediaType: "image",
    uploadFile: vi.fn().mockResolvedValue({ code: 0, data: { url: "remote", object_key: "key", content_type: "image/png", size: 10 } }),
    createPreview: vi.fn().mockResolvedValue("blob:preview"),
    mapAsset: (asset) => asset,
  }));
  return { events, props, scope, uploader };
}

describe("useMediaUploader", () => {
  it("limits files and updates upload placeholders", async () => {
    const { events, props, scope, uploader } = setup({ maxCount: 1 });
    await uploader.processFiles([
      { type: "image/png", name: "a.png", size: 1 },
      { type: "image/png", name: "b.png", size: 2 },
    ]);
    await nextTick();

    expect(props.items).toHaveLength(1);
    expect(props.items[0]).toMatchObject({ url: "remote", uploading: false, error: "" });
    expect(events.some(([event, message]) => event === "notify" && message.includes("上限"))).toBe(true);
    scope.stop();
  });

  it("revokes local previews when removing an item", () => {
    const revoke = vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
    const { props, scope, uploader } = setup({ items: [{ id: "1", previewUrl: "blob:one" }] });

    uploader.removeItem(0);

    expect(revoke).toHaveBeenCalledWith("blob:one");
    expect(props.items).toEqual([]);
    scope.stop();
    revoke.mockRestore();
  });
});
