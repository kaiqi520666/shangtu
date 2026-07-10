import { Boxes, FileVideo, Images, Languages, Shirt, Sparkles, UserRound, Video } from "lucide-vue-next";

export const generationScenarios = [
  { value: "product_suite", label: "商品套图", mediaType: "image", icon: Boxes },
  { value: "product_image", label: "商品详情图", mediaType: "image", icon: Images },
  { value: "outfit", label: "服饰穿搭", mediaType: "image", icon: Shirt },
  { value: "free_image", label: "自由生图", mediaType: "image", icon: Sparkles },
  { value: "product_video", label: "商品视频", mediaType: "video", icon: Video },
  { value: "free_video", label: "自由生视频", mediaType: "video", icon: FileVideo },
  { value: "digital_human", label: "数字人", mediaType: "video", icon: UserRound },
  { value: "video_translation", label: "视频翻译", mediaType: "video", icon: Languages },
];

export const scenarioOptions = [
  { label: "全部场景", value: "" },
  ...generationScenarios.map(({ label, value }) => ({ label, value })),
];

export const scenarioTabs = [
  { label: "全部", value: "" },
  ...generationScenarios.map(({ label, value }) => ({ label, value })),
];

export const scenarioIcons = Object.fromEntries(
  generationScenarios.map(({ value, icon }) => [value, icon]),
);

export const scenarioLabelMap = Object.fromEntries(
  generationScenarios.map(({ value, label }) => [value, label]),
);
