import { describe, expect, it } from "vitest";
import {
  buildProductImageQueue,
  buildProductImageStrategySnapshot,
  buildProductImageUserPrompt,
  createDefaultSelectedModules,
  findProductImageModuleContent,
  normalizeProductImageModules,
  resolveSelectedProductModules,
} from "./productImageStrategy.js";

const modules = [
  { id: "first-screen", name: "首屏主视觉", strategy: "首屏策略" },
  { id: "custom", name: "自定义图种", strategy: "自定义策略" },
];

describe("product image strategy helpers", () => {
  it("resolves selected modules against the current catalog", () => {
    expect(resolveSelectedProductModules(["missing", "custom"], modules)).toEqual([
      "custom",
    ]);
    expect(resolveSelectedProductModules(["missing"], modules)).toEqual([
      "first-screen",
    ]);
    expect(createDefaultSelectedModules()).not.toBe(createDefaultSelectedModules());
  });

  it("builds a strategy snapshot with the selected main image", () => {
    const snapshot = buildProductImageStrategySnapshot({
      settings: {
        platform: "Amazon",
        language: "English",
        ratio: "1:1",
        quality: "1K",
        productInput: "轻便耐用",
      },
      uploadedImages: [{ url: "detail" }, { url: "main" }],
      mainImageIndex: 1,
      selectedModules: ["first-screen"],
    });

    expect(snapshot).toMatchObject({
      scenario: "product_image",
      productInput: "轻便耐用",
      moduleIds: ["first-screen"],
      images: [
        { url: "detail", label: "细节图1" },
        { url: "main", label: "主图" },
      ],
    });
  });

  it("normalizes modules and builds queue prompts", () => {
    const items = normalizeProductImageModules(
      [{ id: "first-screen", content: "突出卖点" }],
      modules,
    );
    const queue = buildProductImageQueue(items, modules);

    expect(items[0]).toEqual({
      id: "first-screen",
      moduleName: "首屏主视觉",
      content: "突出卖点",
      strategy: "首屏策略",
    });
    expect(queue[0]).toMatchObject({ moduleName: "首屏主视觉", index: 1 });
    expect(buildProductImageUserPrompt(queue[0])).toContain(
      "【模块内容】突出卖点",
    );
    expect(findProductImageModuleContent([], modules, "custom")).toMatchObject({
      moduleName: "自定义图种",
      strategy: "自定义策略",
    });
  });
});