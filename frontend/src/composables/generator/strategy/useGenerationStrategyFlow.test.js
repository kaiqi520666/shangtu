import { describe, expect, it, vi } from "vitest";
import { useGenerationStrategyFlow } from "./useGenerationStrategyFlow.js";

describe("useGenerationStrategyFlow", () => {
  it("normalizes and stores a successful strategy response", async () => {
    const flow = useGenerationStrategyFlow({ buildInputSnapshot: () => ({ value: 1 }) });
    const result = await flow.runStrategy({
      snapshot: { value: 1 },
      request: vi.fn().mockResolvedValue({ code: 0, data: { rows: [{ id: "one" }] } }),
      normalizeResult: (data) => ({ brief: "方案", items: data.rows }),
      emptyMessage: "没有方案",
      failureMessage: "生成失败",
    });

    expect(result.ok).toBe(true);
    expect(flow.strategyItems.value).toEqual([{ id: "one" }]);
    expect(flow.strategyBrief.value).toBe("方案");
    expect(flow.workflowStep.value).toBe("strategy-review");
  });

  it("returns to config for empty and failed responses", async () => {
    const flow = useGenerationStrategyFlow();
    const empty = await flow.runStrategy({
      request: vi.fn().mockResolvedValue({ code: 0, data: {} }),
      normalizeResult: () => ({ items: [] }),
      emptyMessage: "没有方案",
      failureMessage: "生成失败",
    });
    expect(empty).toEqual({ ok: false, message: "没有方案" });
    expect(flow.workflowStep.value).toBe("config");

    const error = new Error("offline");
    const failed = await flow.runStrategy({
      request: vi.fn().mockRejectedValue(error),
      normalizeResult: () => ({ items: [] }),
      emptyMessage: "没有方案",
      failureMessage: "生成失败",
    });
    expect(failed).toEqual({ ok: false, message: "生成失败", error });
  });
});
