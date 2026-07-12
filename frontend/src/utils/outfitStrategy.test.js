import { describe, expect, it } from "vitest";
import {
  buildOutfitQueue,
  buildOutfitUserPrompt,
  findOutfitStrategyItem,
  normalizeOutfitStrategyItems,
} from "./outfitStrategy.js";

const scenes = [
  {
    id: "studio",
    label: "纯色棚拍",
    desc: "干净背景",
    strategy: "棚拍策略",
  },
];

describe("outfit strategy helpers", () => {
  it("normalizes strategy details with scene metadata and fidelity", () => {
    const [item] = normalizeOutfitStrategyItems(
      [
        {
          id: "studio",
          pose: "自然站立",
          camera: "平视",
          atmosphere: "明亮",
        },
      ],
      scenes,
    );

    expect(item.name).toBe("纯色棚拍");
    expect(item.description).toBe("干净背景");
    expect(item.strategy).toBe("棚拍策略");
    expect(item.content).toContain("模特姿态：自然站立");
    expect(item.content).toContain("镜头角度：平视");
    expect(item.content).toContain("服装保真约束");
    expect(item.content).toContain("画面氛围：明亮");
  });

  it("builds an indexed queue without mutating strategy items", () => {
    const items = [{ id: "studio", name: "", content: "", strategy: "" }];

    expect(buildOutfitQueue(items, scenes)).toEqual([
      {
        id: "studio",
        name: "纯色棚拍",
        content: "棚拍策略",
        strategy: "棚拍策略",
        index: 1,
      },
    ]);
    expect(items[0]).toEqual({ id: "studio", name: "", content: "", strategy: "" });
  });

  it("builds visible prompts and fallback restored strategy items", () => {
    expect(buildOutfitUserPrompt({ name: "纯色棚拍", content: "保持服装细节" })).toBe(
      "【拍摄场景】纯色棚拍\n【穿搭方案】保持服装细节",
    );
    expect(findOutfitStrategyItem([], scenes, "studio")).toEqual({
      id: "studio",
      name: "纯色棚拍",
      content: "棚拍策略",
      strategy: "棚拍策略",
    });
  });
});
