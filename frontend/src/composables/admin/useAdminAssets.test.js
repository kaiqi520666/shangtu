import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  getAdminAssets: vi.fn(),
  toast: { error: vi.fn(), info: vi.fn(), success: vi.fn() },
}));

vi.mock("@/api/admin.js", () => ({ getAdminAssets: mocks.getAdminAssets }));
vi.mock("@/composables/useToast.js", () => ({ useToast: () => mocks.toast }));
vi.mock("@/composables/useCardActions.js", () => ({
  useCardActions: () => ({
    batchDownload: vi.fn(),
    downloading: { value: false },
    downloadSingleMedia: vi.fn(),
    selectedCardsCount: { value: 0 },
    toggleCardSelection: vi.fn(),
    toggleSelectAllCards: vi.fn(),
    zoomCard: { value: null },
  }),
}));

import { useAdminAssets } from "./useAdminAssets.js";

describe("useAdminAssets", () => {
  beforeEach(() => vi.clearAllMocks());

  it("loads, filters and maps completed assets", async () => {
    mocks.getAdminAssets.mockResolvedValue({
      code: 0,
      data: {
        total: 1,
        items: [{ id: "task-1", result_url: "image", media_type: "image", user_email: "a@example.com" }],
      },
    });
    const controller = useAdminAssets();
    controller.state.scenario = "outfit";

    await controller.loadAssets();

    expect(mocks.getAdminAssets).toHaveBeenCalledWith(expect.objectContaining({ scenario: "outfit", page: 1 }));
    expect(controller.state.items[0]).toMatchObject({ taskId: "task-1", dataUrl: "image", userEmail: "a@example.com" });
  });
});
