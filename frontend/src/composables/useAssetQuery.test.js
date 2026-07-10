import { beforeEach, describe, expect, it, vi } from "vitest";

const listAssets = vi.hoisted(() => vi.fn());

vi.mock("@/api/assets.js", () => ({ listAssets }));

import { mapAssetItem, useAssetQuery } from "./useAssetQuery.js";

describe("useAssetQuery", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    listAssets.mockResolvedValue({ code: 0, data: { items: [], total: 0 } });
  });

  it("maps audio metadata to the shared asset shape", () => {
    expect(mapAssetItem({
      task_id: "audio-1",
      media_type: "audio",
      result_url: "https://example.com/audio.mp3",
      title: "口播",
      source: "upload",
      duration_seconds: 12,
      size: 2048,
      content_type: "audio/mpeg",
    })).toMatchObject({
      id: "audio-1",
      taskId: "audio-1",
      mediaType: "audio",
      source: "upload",
      durationSeconds: 12,
      size: 2048,
      contentType: "audio/mpeg",
      status: "done",
    });
  });

  it("resets an incompatible scenario when media type changes", async () => {
    const query = useAssetQuery();
    query.scenario.value = "product_video";

    await query.changeMediaType("image");

    expect(query.scenario.value).toBe("");
    expect(listAssets).toHaveBeenCalledWith(expect.objectContaining({ media_type: "image", scenario: "" }));
  });

  it("hides scenario filters for audio assets", async () => {
    const query = useAssetQuery();
    await query.changeMediaType("audio");
    expect(query.scenarioFilters.value).toEqual([]);
  });
});
