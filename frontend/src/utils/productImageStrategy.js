import { buildProductAnalyzeImages } from "@/utils/analyzeImages.js";

const DEFAULT_SELECTED_MODULES = [
  "first-screen",
  "core-selling",
  "use-scenario",
  "multi-angle",
  "detail-zoom",
  "ambient-scene",
];

export function createDefaultSelectedModules() {
  return [...DEFAULT_SELECTED_MODULES];
}

export function resolveSelectedProductModules(moduleIds, availableModules) {
  const catalogIds = availableModules.map((module) => module.id);
  const selected = moduleIds.filter((id) => catalogIds.includes(id));
  if (selected.length > 0) return selected;
  const defaults = DEFAULT_SELECTED_MODULES.filter((id) =>
    catalogIds.includes(id),
  );
  return defaults.length > 0 ? defaults : catalogIds.slice(0, 6);
}

export function findProductImageModule(availableModules, id) {
  return availableModules.find((module) => module.id === id) || null;
}

export function getProductImageModuleName(availableModules, id) {
  return findProductImageModule(availableModules, id)?.name || id || "详情图";
}

export function getProductImageModuleStrategy(availableModules, id) {
  return findProductImageModule(availableModules, id)?.strategy || "";
}

export function buildProductImageStrategySnapshot({
  settings,
  uploadedImages,
  mainImageIndex,
  selectedModules,
}) {
  return {
    scenario: "product_image",
    images: buildProductAnalyzeImages(uploadedImages, mainImageIndex),
    platform: settings.platform,
    language: settings.language,
    ratio: settings.ratio,
    quality: settings.quality,
    productInput: settings.productInput,
    moduleIds: [...selectedModules],
  };
}

export function getActiveProductImageModuleIds(items) {
  return items.map((module) => module.id).filter(Boolean);
}

export function buildProductImageQueue(items, availableModules) {
  return items.map((item, index) => ({
    ...item,
    moduleName:
      item.moduleName || getProductImageModuleName(availableModules, item.id),
    content: item.content || "",
    strategy: item.strategy || "",
    index: index + 1,
  }));
}

export function buildProductImageUserPrompt(item) {
  return [
    `【图种】${item.moduleName}`,
    item.strategy ? `【视觉策略】${item.strategy}` : "",
    item.content ? `【模块内容】${item.content}` : "",
  ]
    .filter(Boolean)
    .join("\n");
}

export function normalizeProductImageModules(modules, availableModules) {
  return modules.map((module, index) => {
    const fallback = findProductImageModule(availableModules, module.id);
    return {
      id: module.id || fallback?.id || `module-${index + 1}`,
      moduleName: module.moduleName || fallback?.name || `模块 ${index + 1}`,
      content: module.content || "",
      strategy: module.strategy || fallback?.strategy || "",
    };
  });
}

export function findProductImageModuleContent(items, availableModules, typeId) {
  return (
    items.find((module) => module.id === typeId) || {
      id: typeId,
      moduleName: getProductImageModuleName(availableModules, typeId),
      content: getProductImageModuleStrategy(availableModules, typeId),
      strategy: getProductImageModuleStrategy(availableModules, typeId),
    }
  );
}