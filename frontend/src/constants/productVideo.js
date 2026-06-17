export const videoDemoTypes = [
  {
    typeId: "ugc_seeding",
    title: "UGC 种草",
    subtitle: "用户视角真实分享体验",
    inputMode: "first_frame",
    uploadTitle: "上传视频开头画面",
    uploadHint: "建议上传产品在真实场景里的首帧图。",
    videoUrl: "https://youjia-bucket.oss-cn-hongkong.aliyuncs.com/system/product-video-demos/videos/ugc_seeding.mp4",
    posterUrl: "https://youjia-bucket.oss-cn-hongkong.aliyuncs.com/system/product-video-demos/posters/ugc_seeding.jpg",
  },
  {
    typeId: "short_drama",
    title: "带货短剧",
    subtitle: "短剧情节植入产品",
    inputMode: "reference_images",
    uploadTitle: "上传产品/人物/场景参考图",
    uploadHint: "建议上传产品图、使用场景图或人物参考图。",
    videoUrl: "https://youjia-bucket.oss-cn-hongkong.aliyuncs.com/system/product-video-demos/videos/short_drama.mp4",
    posterUrl: "https://youjia-bucket.oss-cn-hongkong.aliyuncs.com/system/product-video-demos/posters/short_drama.jpg",
  },
  {
    typeId: "product_demo",
    title: "产品演示",
    subtitle: "多角度展示 + 使用演示",
    inputMode: "reference_images",
    uploadTitle: "上传产品参考图",
    uploadHint: "建议上传多张不同角度或细节图，帮助视频稳定还原产品。",
    videoUrl: "https://youjia-bucket.oss-cn-hongkong.aliyuncs.com/system/product-video-demos/videos/product_demo.mp4",
    posterUrl: "https://youjia-bucket.oss-cn-hongkong.aliyuncs.com/system/product-video-demos/posters/product_demo.jpg",
  },
  {
    typeId: "product_talk",
    title: "产品口播",
    subtitle: "面对镜头讲解产品卖点",
    inputMode: "first_frame",
    uploadTitle: "上传口播首帧图",
    uploadHint: "适合上传人物持产品、产品近景或口播画面首帧。",
    videoUrl: "https://youjia-bucket.oss-cn-hongkong.aliyuncs.com/system/product-video-demos/videos/product_talk.mp4",
    posterUrl: "https://youjia-bucket.oss-cn-hongkong.aliyuncs.com/system/product-video-demos/posters/product_talk.jpg",
  },
  {
    typeId: "tvc_ad",
    title: "TVC广告",
    subtitle: "品牌广告片质感",
    inputMode: "reference_images",
    uploadTitle: "上传产品/场景参考图",
    uploadHint: "建议上传产品主图、品牌场景图和质感细节图。",
    videoUrl: "https://youjia-bucket.oss-cn-hongkong.aliyuncs.com/system/product-video-demos/videos/tvc_ad.mp4",
    posterUrl: "https://youjia-bucket.oss-cn-hongkong.aliyuncs.com/system/product-video-demos/posters/tvc_ad.jpg",
  },
  {
    typeId: "pain_solution",
    title: "痛点解决",
    subtitle: "痛点场景到产品解决",
    inputMode: "first_last_frame",
    uploadTitle: "上传问题与解决画面",
    uploadHint: "左图是问题画面，右图是产品解决后的效果画面。",
    videoUrl: "https://youjia-bucket.oss-cn-hongkong.aliyuncs.com/system/product-video-demos/videos/pain_solution.mp4",
    posterUrl: "https://youjia-bucket.oss-cn-hongkong.aliyuncs.com/system/product-video-demos/posters/pain_solution.jpg",
  },
  {
    typeId: "unboxing",
    title: "开箱种草",
    subtitle: "第一视角拆包惊喜体验",
    inputMode: "first_last_frame",
    uploadTitle: "上传未开箱与开箱后画面",
    uploadHint: "左图是包装/未开箱，右图是开箱后产品展示。",
    videoUrl: "https://youjia-bucket.oss-cn-hongkong.aliyuncs.com/system/product-video-demos/videos/unboxing.mp4",
    posterUrl: "https://youjia-bucket.oss-cn-hongkong.aliyuncs.com/system/product-video-demos/posters/unboxing.jpg",
  },
  {
    typeId: "reaction",
    title: "反应展示",
    subtitle: "首次使用惊喜反应",
    inputMode: "first_last_frame",
    uploadTitle: "上传展示前与反应画面",
    uploadHint: "左图是使用前/展示前，右图是惊喜反应或效果后。",
    videoUrl: "https://youjia-bucket.oss-cn-hongkong.aliyuncs.com/system/product-video-demos/videos/reaction.mp4",
    posterUrl: "https://youjia-bucket.oss-cn-hongkong.aliyuncs.com/system/product-video-demos/posters/reaction.jpg",
  },
];

export const videoMarketOptions = [
  { value: "global", label: "全球/其他" },
  { value: "north_america", label: "北美" },
  { value: "europe", label: "欧洲" },
  { value: "china", label: "中国" },
  { value: "japan", label: "日本" },
  { value: "korea", label: "韩国" },
  { value: "southeast_asia", label: "东南亚" },
  { value: "brazil", label: "巴西" },
];

export const videoLanguageOptions = [
  { value: "english", label: "英语" },
  { value: "chinese", label: "中文" },
  { value: "japanese", label: "日语" },
  { value: "korean", label: "韩语" },
  { value: "spanish", label: "西班牙语" },
  { value: "portuguese", label: "葡萄牙语" },
  { value: "music_only", label: "纯音乐无口播" },
];

export const videoSizeOptions = [
  { value: "tiktok_9_16", label: "TikTok/Reels · 9:16", aspectRatio: "9:16" },
  { value: "rednote_douyin_9_16", label: "小红书/抖音 · 9:16", aspectRatio: "9:16" },
  { value: "taobao_1_1", label: "淘宝主图视频 · 1:1", aspectRatio: "1:1" },
  { value: "youtube_amazon_16_9", label: "YouTube/亚马逊 · 16:9", aspectRatio: "16:9" },
];

export const videoResolutionOptions = [
  { value: "480p", label: "480p", subtitle: "快速预览" },
  { value: "720p", label: "720p", subtitle: "默认推荐" },
  { value: "1080p", label: "1080p", subtitle: "高清成片" },
];

export const defaultVideoCreditCosts = {
  "480p": 1,
  "720p": 2,
  "1080p": 4,
};

export function getVideoDemoType(typeId) {
  return videoDemoTypes.find((item) => item.typeId === typeId) || videoDemoTypes[0];
}

export function getVideoCreditCost({ resolution = "720p", duration = 6, costs = defaultVideoCreditCosts } = {}) {
  const unitCost = Number(costs[resolution] ?? defaultVideoCreditCosts[resolution]);
  const seconds = Math.max(4, Math.min(15, Number(duration || 6)));
  if (!Number.isFinite(unitCost) || unitCost <= 0) return null;
  return unitCost * seconds;
}
