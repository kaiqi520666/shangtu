// @vitest-environment jsdom

import { effectScope, ref } from "vue";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useAudioAssets } from "./useAudioAssets.js";
import { usePhotoAvatars } from "./usePhotoAvatars.js";
import {
  deleteDigitalHumanAudioAsset,
  getDigitalHumanAudioAssets,
  getPhotoAvatarTasks,
  getPhotoAvatars,
  pollPhotoAvatarTask,
} from "@/api/digitalHuman.js";

vi.mock("@/api/digitalHuman.js", () => ({
  deleteDigitalHumanAudioAsset: vi.fn(),
  deletePhotoAvatar: vi.fn(),
  deletePhotoAvatarTask: vi.fn(),
  getDigitalHumanAudioAssets: vi.fn(),
  getPhotoAvatarTasks: vi.fn(),
  getPhotoAvatars: vi.fn(),
  pollPhotoAvatarTask: vi.fn(),
  uploadDigitalHumanAudioAsset: vi.fn(),
  uploadPhotoAvatar: vi.fn(),
}));

const listResult = (items) => ({ code: 0, data: { items, total: items.length } });

describe("digital human user assets", () => {
  beforeEach(() => vi.clearAllMocks());
  afterEach(() => vi.useRealTimers());

  it("polls active photo avatar tasks and refreshes lists", async () => {
    vi.useFakeTimers();
    getPhotoAvatars.mockResolvedValue(listResult([]));
    getPhotoAvatarTasks.mockResolvedValue(listResult([{ id: "task-1", status: "processing" }]));
    pollPhotoAvatarTask.mockResolvedValue({ code: 0 });
    const scope = effectScope();
    const photo = scope.run(() => usePhotoAvatars({ selectedAvatar: ref(null), notifyError: vi.fn() }));

    await photo.init();
    await vi.advanceTimersByTimeAsync(5000);

    expect(pollPhotoAvatarTask).toHaveBeenCalledWith("task-1");
    expect(getPhotoAvatarTasks).toHaveBeenCalledTimes(2);
    scope.stop();
  });

  it("clears the selected uploaded audio after deletion", async () => {
    getDigitalHumanAudioAssets.mockResolvedValue(listResult([]));
    deleteDigitalHumanAudioAsset.mockResolvedValue({ code: 0 });
    vi.spyOn(window, "confirm").mockReturnValue(true);
    const selectedVoice = ref({ mode: "upload", audio_asset_id: "audio-1" });
    const scope = effectScope();
    const audio = scope.run(() => useAudioAssets({ selectedVoice, notify: vi.fn() }));

    await audio.remove({ id: "audio-1" });

    expect(selectedVoice.value).toBeNull();
    expect(getDigitalHumanAudioAssets).toHaveBeenCalledOnce();
    scope.stop();
  });
});
