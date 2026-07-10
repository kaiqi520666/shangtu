IMAGE_SCENARIOS = {"product_suite", "product_image", "outfit", "free_image"}
VIDEO_SCENARIOS = {"product_video", "free_video", "digital_human", "video_translation"}
AUDIO_SCENARIOS = {"voiceover"}
SUPPORTED_GENERATION_SCENARIOS = IMAGE_SCENARIOS | VIDEO_SCENARIOS | AUDIO_SCENARIOS

SCENARIO_TITLE_PREFIX = {
    "product_suite": "商品套图",
    "product_image": "商品详情图",
    "outfit": "服饰穿搭",
    "free_image": "自由生图",
    "product_video": "商品视频",
    "free_video": "自由生视频",
    "digital_human": "数字人",
    "video_translation": "视频翻译",
    "voiceover": "AI配音",
}
