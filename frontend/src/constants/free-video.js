export const freeVideoInputModes = [
  {
    value: "text_to_video",
    label: "文生视频",
    description: "输入提示词直接生成视频",
    uploadTitle: "",
    addText: "",
    hintText: "",
  },
  {
    value: "image_to_video",
    label: "首帧图生视频",
    description: "从 1 张首帧图开始生成动态视频",
    uploadTitle: "首帧图",
    addText: "添加首帧图",
    hintText: "必须上传 1 张",
  },
  {
    value: "reference_to_video",
    label: "参考图生视频",
    description: "用 1-9 张参考图生成视频",
    uploadTitle: "参考图",
    addText: "添加参考图",
    hintText: "支持 1-9 张",
  },
  {
    value: "video_edit",
    label: "爆款复刻",
    description: "参考爆款节奏生成原创版本",
    uploadTitle: "参考图",
    addText: "添加参考图",
    hintText: "可选，最多 5 张",
  },
];

export const freeVideoRatioOptions = [
  { value: "9:16", label: "9:16", description: "竖屏短视频" },
  { value: "16:9", label: "16:9", description: "横屏视频" },
  { value: "1:1", label: "1:1", description: "方形视频" },
  { value: "4:3", label: "4:3", description: "横向内容" },
  { value: "3:4", label: "3:4", description: "竖向内容" },
];

export const freeVideoAudioOptions = [
  { value: "auto", label: "AI 自动处理", description: "由模型重组声音策略" },
  { value: "origin", label: "保留原声", description: "尽量沿用参考视频声音" },
];

export function getFreeVideoInputMode(mode) {
  return freeVideoInputModes.find((item) => item.value === mode) || freeVideoInputModes[0];
}

export function makeFreeVideoTitle(prompt) {
  const compact = (prompt || "").trim().replace(/\s+/g, " ");
  if (!compact) return "自由生视频";
  return compact.length > 20 ? `${compact.slice(0, 20)}...` : compact;
}
