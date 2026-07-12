import { describe, expect, it } from "vitest";
import {
  buildSuiteQueue,
  buildSuiteStrategySnapshot,
  buildSuiteUserPrompt,
  createSuiteStructureFromCatalog,
  findSuiteStrategyItem,
  normalizeSuiteStrategyItems,
  syncSuiteStructureWithCatalog,
} from "./productSuiteStrategy.js";

const catalog = [
  {
    id: "white-bg",
    name: "白底图",
    description: "干净背景",
    strategy: "白底策略",
    defaultCount: 2,
    maxCount: 3,
  },
];

describe("product suite strategy helpers", () => {
  it("creates and synchronizes editable catalog structure", () => {
    expect(createSuiteStructureFromCatalog(catalog)[0]).toMatchObject({
      id: "white-bg",
      enabled: true,
      count: 2,
    });
    expect(
      syncSuiteStructureWithCatalog(
        [{ id: "white-bg", enabled: false, count: 9 }],
        catalog,
      )[0],
    ).toMatchObject({ enabled: false, count: 3 });
  });

  it("builds a strategy snapshot with normalized structure and images", () => {
    const snapshot = buildSuiteStrategySnapshot({
      settings: {
        platform: "Amazon",
        language: "English",
        ratio: "1:1",
        quality: "1K",
        productInput: "轻便耐用",
      },
      uploadedImages: [{ url: "main" }, { url: "detail" }],
      mainImageIndex: 1,
      structure: [{ id: "white-bg", enabled: 1, count: "2" }],
    });

    expect(snapshot).toMatchObject({
      scenario: "product_suite",
      productInput: "轻便耐用",
      images: [
        { url: "main", label: "细节图1" },
        { url: "detail", label: "主图" },
      ],
      structure: [{ id: "white-bg", enabled: true, count: 2 }],
    });
  });

  it("normalizes strategies and expands queue prompts", () => {
    const items = normalizeSuiteStrategyItems(
      [{ id: "white-bg", content: "突出主体", count: 2 }],
      catalog,
    );
    const queue = buildSuiteQueue(items, catalog);

    expect(items[0]).toMatchObject({
      name: "白底图",
      description: "干净背景",
      strategy: "白底策略",
      count: 2,
      enabled: true,
    });
    expect(queue.map((item) => item.cardTitle)).toEqual(["白底图 1", "白底图 2"]);
    expect(buildSuiteUserPrompt(queue[0])).toContain("【本张序号】1/2");
    expect(findSuiteStrategyItem([], catalog, "white-bg")).toMatchObject({
      name: "白底图",
      strategy: "白底策略",
    });
  });
});
