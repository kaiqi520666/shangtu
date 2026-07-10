import { beforeEach, describe, expect, it, vi } from "vitest";

const api = vi.hoisted(() => ({
  deleteOutfitModel: vi.fn(),
  listOutfitModels: vi.fn(),
  uploadOutfitModel: vi.fn(),
}));

vi.mock("@/api/outfit.js", () => api);

import { useOutfitModels } from "./useOutfitModels.js";

describe("useOutfitModels", () => {
  const toast = { error: vi.fn(), info: vi.fn(), success: vi.fn() };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads and selects the first normalized model", async () => {
    api.listOutfitModels.mockResolvedValue({
      code: 0,
      data: [{ id: "model-1", name: "模特", image_url: "image", can_delete: true }],
    });
    const models = useOutfitModels({ toast });

    await models.loadOutfitModels();

    expect(models.modelLibrary.value[0]).toMatchObject({ id: "model-1", image: "image", canDelete: true });
    expect(models.selectedModelId.value).toBe("model-1");
  });

  it("removes a deletable model and selects the next one", async () => {
    api.deleteOutfitModel.mockResolvedValue({ code: 0 });
    const models = useOutfitModels({ toast });
    models.modelLibrary.value = [
      { id: "a", canDelete: true },
      { id: "b", canDelete: false },
    ];
    models.selectedModelId.value = "a";

    await models.deleteModel("a");

    expect(models.modelLibrary.value.map((item) => item.id)).toEqual(["b"]);
    expect(models.selectedModelId.value).toBe("b");
  });
});
