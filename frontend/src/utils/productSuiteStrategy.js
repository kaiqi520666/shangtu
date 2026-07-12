import { buildProductAnalyzeImages } from "@/utils/analyzeImages.js";

export function createSuiteStructureFromCatalog(items) {
  return items.map((item) => ({
    ...item,
    enabled: true,
    count: item.defaultCount,
  }));
}

export function clampSuiteStructureCount(count, maxCount) {
  return Math.min(Math.max(1, Number(count) || 1), maxCount);
}

export function syncSuiteStructureWithCatalog(currentItems, catalogItems) {
  return catalogItems.map((catalogItem) => {
    const current = currentItems.find((item) => item.id === catalogItem.id);
    return {
      ...catalogItem,
      enabled: current ? Boolean(current.enabled) : true,
      count: current
        ? clampSuiteStructureCount(current.count, catalogItem.maxCount)
        : catalogItem.defaultCount,
    };
  });
}

export function findSuiteStructure(catalogItems, id) {
  return catalogItems.find((item) => item.id === id) || null;
}

export function getSuiteStructureName(catalogItems, id) {
  return findSuiteStructure(catalogItems, id)?.name || id || "商品套图";
}

export function getSuiteStructureStrategy(catalogItems, id) {
  return findSuiteStructure(catalogItems, id)?.strategy || "商品套图生成";
}

export function buildSuiteStrategySnapshot({
  settings,
  uploadedImages,
  mainImageIndex,
  structure,
}) {
  return {
    scenario: "product_suite",
    images: buildProductAnalyzeImages(uploadedImages, mainImageIndex),
    platform: settings.platform,
    language: settings.language,
    ratio: settings.ratio,
    quality: settings.quality,
    productInput: settings.productInput,
    structure: structure.map((item) => ({
      id: item.id,
      enabled: Boolean(item.enabled),
      count: Number(item.count) || 0,
    })),
  };
}

export function buildSuiteQueue(items, catalogItems) {
  return items.flatMap((item) => {
    const count = Math.max(0, Number(item.count) || 0);
    const name = item.name || getSuiteStructureName(catalogItems, item.id);
    return Array.from({ length: count }, (_, index) => ({
      ...item,
      name,
      content: item.content || "",
      strategy:
        item.strategy || getSuiteStructureStrategy(catalogItems, item.id),
      index: index + 1,
      total: count,
      cardTitle: count > 1 ? `${name} ${index + 1}` : name,
    }));
  });
}

export function buildSuiteUserPrompt(item) {
  return [
    `【套图类型】${item.name}`,
    item.strategy ? `【视觉策略】${item.strategy}` : "",
    item.content ? `【画面要求】${item.content}` : "",
    item.total > 1
      ? `【本张序号】${item.index}/${item.total}，同类型多张图需要构图、角度或场景有区分。`
      : "",
  ]
    .filter(Boolean)
    .join("\n");
}

export function normalizeSuiteStrategyItems(items, catalogItems) {
  return items.map((item, index) => {
    const fallback = findSuiteStructure(catalogItems, item.id);
    return {
      id: item.id || fallback?.id || `suite-${index + 1}`,
      name: item.name || fallback?.name || `套图 ${index + 1}`,
      description: item.description || fallback?.description || "",
      strategy: item.strategy || fallback?.strategy || "",
      content: item.content || "",
      count: Math.max(1, Number(item.count) || fallback?.defaultCount || 1),
      enabled: true,
    };
  });
}

export function findSuiteStrategyItem(items, catalogItems, typeId) {
  return (
    items.find((item) => item.id === typeId) || {
      id: typeId,
      name: getSuiteStructureName(catalogItems, typeId),
      content: getSuiteStructureStrategy(catalogItems, typeId),
      strategy: getSuiteStructureStrategy(catalogItems, typeId),
    }
  );
}
