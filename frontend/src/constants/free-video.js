export const freeVideoRatioOptions = [
  { value: "9:16", label: "9:16", description: "竖屏短视频" },
  { value: "16:9", label: "16:9", description: "横屏视频" },
  { value: "1:1", label: "1:1", description: "方形视频" },
  { value: "4:3", label: "4:3", description: "横向内容" },
  { value: "3:4", label: "3:4", description: "竖向内容" },
];

export function makeFreeVideoTitle(prompt) {
  const compact = (prompt || "").trim().replace(/\s+/g, " ");
  if (!compact) return "自由生视频";
  return compact.length > 20 ? `${compact.slice(0, 20)}...` : compact;
}
