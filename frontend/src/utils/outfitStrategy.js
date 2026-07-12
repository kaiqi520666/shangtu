const DEFAULT_SCENE_STRATEGY = "服饰穿搭场景生成";
const DEFAULT_FIDELITY =
  "服装保真约束：保持上传服装的颜色、版型、材质、图案、长度、领口、袖型、廓形和核心外观一致，不换款不改款。";

export function findOutfitScene(scenes, id) {
  const preset = scenes.find((scene) => scene.id === id);
  return {
    id,
    label: preset?.label || id || "服饰穿搭图",
    description: preset?.desc || "",
    strategy: preset?.strategy || DEFAULT_SCENE_STRATEGY,
  };
}

export function getOutfitSceneName(scenes, id) {
  return findOutfitScene(scenes, id).label;
}

export function getOutfitSceneStrategy(scenes, id) {
  return findOutfitScene(scenes, id).strategy;
}

export function normalizeOutfitStrategyItems(items, scenes) {
  return items.map((item, index) => {
    const scene = findOutfitScene(scenes, item.id);
    const content = [
      item.content,
      item.pose && `模特姿态：${item.pose}`,
      item.camera && `镜头角度：${item.camera}`,
      item.fidelity || DEFAULT_FIDELITY,
      item.atmosphere && `画面氛围：${item.atmosphere}`,
    ]
      .filter(Boolean)
      .join("\n");
    return {
      id: item.id || scene.id || `outfit-${index + 1}`,
      name: item.name || scene.label || `场景 ${index + 1}`,
      description: item.description || scene.description || "",
      strategy: item.strategy || scene.strategy || "",
      content,
    };
  });
}

export function buildOutfitQueue(items, scenes) {
  return items.map((item, index) => ({
    ...item,
    id: item.id,
    name: item.name || getOutfitSceneName(scenes, item.id),
    content:
      item.content || item.strategy || getOutfitSceneStrategy(scenes, item.id),
    strategy: item.strategy || getOutfitSceneStrategy(scenes, item.id),
    index: index + 1,
  }));
}

export function buildOutfitUserPrompt(item) {
  return [
    `【拍摄场景】${item.name}`,
    item.content ? `【穿搭方案】${item.content}` : "",
  ]
    .filter(Boolean)
    .join("\n");
}

export function findOutfitStrategyItem(items, scenes, typeId) {
  return (
    items.find((item) => item.id === typeId) || {
      id: typeId,
      name: getOutfitSceneName(scenes, typeId),
      content: getOutfitSceneStrategy(scenes, typeId),
      strategy: getOutfitSceneStrategy(scenes, typeId),
    }
  );
}
