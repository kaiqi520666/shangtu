// @vitest-environment jsdom

import { ref } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

const zip = vi.hoisted(() => ({
  constructor: vi.fn(),
  file: vi.fn(),
  generateAsync: vi.fn(async () => new Blob(["zip"])),
}));

vi.mock("jszip", () => ({
  default: class MockZip {
    constructor() {
      zip.constructor();
    }
    file(...args) {
      return zip.file(...args);
    }
    generateAsync(...args) {
      return zip.generateAsync(...args);
    }
  },
}));
vi.mock("@/stores/auth.js", () => ({ useAuthStore: () => ({ token: "token" }) }));

import { useCardActions } from "./useCardActions.js";

describe("useCardActions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: true, blob: async () => new Blob(["image"], { type: "image/png" }) })));
    URL.createObjectURL = vi.fn(() => "blob:zip");
    URL.revokeObjectURL = vi.fn();
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  });

  it("loads JSZip only when a multi-card download starts", async () => {
    const cards = ref([
      { id: "1", selected: true, status: "done", dataUrl: "one" },
      { id: "2", selected: true, status: "done", dataUrl: "two" },
    ]);
    const actions = useCardActions({
      outputCards: cards,
      currentTaskTitle: ref("任务"),
      getCardName: (card) => card.id,
      getDownloadUrl: (card) => card.dataUrl,
      getFetchHeaders: () => ({}),
      toast: { error: vi.fn(), info: vi.fn(), success: vi.fn() },
    });

    expect(zip.constructor).not.toHaveBeenCalled();
    await actions.batchDownload();
    expect(zip.constructor).toHaveBeenCalledOnce();
    expect(zip.file).toHaveBeenCalledTimes(2);
  });

  it("uses the audio response type as the downloaded file extension", async () => {
    const cards = ref([{ id: "1", selected: true, status: "done", dataUrl: "audio", downloading: false }]);
    const actions = useCardActions({
      outputCards: cards,
      currentTaskTitle: ref("配音"),
      getCardName: () => "口播",
      getDownloadUrl: () => "/asset/audio/1/download",
      toast: { error: vi.fn(), info: vi.fn(), success: vi.fn() },
    });
    fetch.mockResolvedValueOnce({ ok: true, blob: async () => new Blob(["audio"], { type: "audio/mpeg" }) });

    await actions.downloadSingleMedia(cards.value[0]);

    expect(HTMLAnchorElement.prototype.click).toHaveBeenCalled();
  });
});
