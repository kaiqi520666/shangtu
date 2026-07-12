import { describe, expect, it, vi } from "vitest";
import { useGenerationCards } from "./useGenerationCards.js";

describe("useGenerationCards polling", () => {
  it("shows a retry warning after consecutive failures and clears it on success", async () => {
    const getTask = vi.fn()
      .mockRejectedValueOnce(new Error("offline"))
      .mockRejectedValueOnce(new Error("offline"))
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValue({ code: 0, data: { status: "processing", progress: 20 } });
    const cards = useGenerationCards({ getTask, preloadResult: false });
    const card = cards.createCard({ typeId: "main" });
    card.taskId = "task-1";

    await cards.pollCardOnce(card);
    await cards.pollCardOnce(card);
    expect(card.stalledWarning).toBe("");

    await cards.pollCardOnce(card);
    expect(card.stalledWarning).toBe("连接异常，正在重试");
    expect(card.status).toBe("pending");

    await cards.pollCardOnce(card);
    expect(card.pollFailureCount).toBe(0);
    expect(card.stalledWarning).toBe("");
    expect(card.status).toBe("processing");
  });
});
