export const platformOptions = [
  { value: '亚马逊', label: '亚马逊' },
  { value: '淘宝天猫1688', label: '淘宝天猫1688' },
  { value: 'Temu', label: 'Temu' },
  { value: 'TikTok Shop', label: 'TikTok Shop' },
  { value: '拼多多', label: '拼多多' },
  { value: '抖音电商', label: '抖音电商' },
  { value: 'OZON', label: 'OZON' },
  { value: '独立站', label: '独立站' },
  { value: 'Shopee', label: 'Shopee' },
  { value: '阿里国际站', label: '阿里国际站' },
  { value: '速卖通', label: '速卖通' },
  { value: 'SHEIN', label: 'SHEIN' },
  { value: '京东', label: '京东' },
  { value: '美客多', label: '美客多' },
  { value: 'Coupang', label: 'Coupang' },
  { value: 'Wayfair', label: 'Wayfair' },
]

export const languageOptions = [
  { value: '英文', label: '英文' },
  { value: '中文', label: '中文' },
  { value: '俄语', label: '俄语' },
  { value: '西语', label: '西语' },
  { value: '德语', label: '德语' },
  { value: '日语', label: '日语' },
  { value: '韩语', label: '韩语' },
  { value: '葡萄牙语', label: '葡萄牙语' },
  { value: '印尼语', label: '印尼语' },
  { value: '泰语', label: '泰语' },
  { value: '无文字', label: '无文字' },
]

export const ratioOptions = [
  { value: '1:1', label: '1:1', description: '正方形' },
  { value: '3:2', label: '3:2', description: '横图' },
  { value: '2:3', label: '2:3', description: '竖图' },
  { value: '4:3', label: '4:3', description: '横图' },
  { value: '3:4', label: '3:4', description: '竖图' },
  { value: '5:4', label: '5:4', description: '横图' },
  { value: '4:5', label: '4:5', description: '竖图' },
  { value: '16:9', label: '16:9', description: '横图' },
  { value: '9:16', label: '9:16', description: '竖图' },
  { value: '2:1', label: '2:1', description: '横幅' },
  { value: '1:2', label: '1:2', description: '长竖图' },
  { value: '21:9', label: '21:9', description: '横图' },
  { value: '9:21', label: '9:21', description: '长竖图' },
]

export const qualityOptions = [
  { value: '1K', title: '1K', subtitle: '更快' },
  { value: '2K', title: '2K', subtitle: '推荐' },
  { value: '4K', title: '4K', subtitle: '更精细' },
]

export const productDetailPreviewSlides = [
  {
    caption: '从商品图片到高转化详情图，一次生成多类电商视觉模块。',
    sourceImage: 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=360&q=80',
    resultImages: [
      'https://images.unsplash.com/photo-1541807084-5c52b6b3adef?auto=format&fit=crop&w=420&q=80',
      'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=420&q=80',
      'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=420&q=80',
    ],
  },
  {
    caption: '卖点图、规格图、售后保障图统一排版，适配多平台详情页。',
    sourceImage: 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=360&q=80',
    resultImages: [
      'https://images.unsplash.com/photo-1545127398-14699f92334b?auto=format&fit=crop&w=420&q=80',
      'https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=420&q=80',
      'https://images.unsplash.com/photo-1505236273191-1dce886b01e9?auto=format&fit=crop&w=420&q=80',
    ],
  },
]

export const resolutionMap = {
  '1:1': {
    '1K': [1024, 1024],
    '2K': [2048, 2048],
  },
  '3:2': {
    '1K': [1536, 1024],
    '2K': [2048, 1360],
  },
  '2:3': {
    '1K': [1024, 1536],
    '2K': [1360, 2048],
  },
  '4:3': {
    '1K': [1024, 768],
    '2K': [2048, 1536],
  },
  '3:4': {
    '1K': [768, 1024],
    '2K': [1536, 2048],
  },
  '5:4': {
    '1K': [1280, 1024],
    '2K': [2560, 2048],
  },
  '4:5': {
    '1K': [1024, 1280],
    '2K': [2048, 2560],
  },
  '16:9': {
    '1K': [1536, 864],
    '2K': [2048, 1152],
    '4K': [3840, 2160],
  },
  '9:16': {
    '1K': [864, 1536],
    '2K': [1152, 2048],
    '4K': [2160, 3840],
  },
  '2:1': {
    '1K': [2048, 1024],
    '2K': [2688, 1344],
    '4K': [3840, 1920],
  },
  '1:2': {
    '1K': [1024, 2048],
    '2K': [1344, 2688],
    '4K': [1920, 3840],
  },
  '21:9': {
    '1K': [2016, 864],
    '2K': [2688, 1152],
    '4K': [3840, 1648],
  },
  '9:21': {
    '1K': [864, 2016],
    '2K': [1152, 2688],
    '4K': [1648, 3840],
  },
}

export function getSupportedQualities(ratio) {
  return Object.keys(resolutionMap[ratio] || {})
}

export function isQualitySupported(ratio, quality) {
  return Boolean(resolutionMap[ratio]?.[quality])
}

export function resolveQuality(ratio, requestedQuality) {
  if (isQualitySupported(ratio, requestedQuality)) return requestedQuality
  const supported = getSupportedQualities(ratio)
  if (supported.length === 0) return null
  if (supported.includes('2K')) return '2K'
  if (supported.includes('1K')) return '1K'
  return supported[0]
}

export function formatImageLabel({ ratio = '1:1', quality = '1K' } = {}) {
  const ratioOption = ratioOptions.find((option) => option.value === ratio) || ratioOptions[0]
  const effectiveQuality = resolveQuality(ratioOption.value, quality) || quality
  const dims = resolutionMap[ratioOption.value]?.[effectiveQuality]
  if (!dims) {
    return `${effectiveQuality} / ${ratioOption.label}`
  }
  const [width, height] = dims
  return `${effectiveQuality} / ${ratioOption.label} / ${width}x${height}`
}

export const availableModules = [
  { id: 'first-screen', name: '首屏主视觉', desc: '极简大图与大字报，第一眼传递核心卖点价值。', strategy: '大标题聚焦，高饱和度背板突显商品核心形态。' },
  { id: 'core-selling', name: '核心卖点图', desc: '突出商品三大硬核优势，多点对照打消疑虑。', strategy: '三栏目清单排版，配图层级鲜明。' },
  { id: 'use-scenario', name: '使用场景图', desc: '呈现真实使用状态或家居融入。', strategy: '融合淡雅环境投影，拉近用户心理距离。' },
  { id: 'multi-angle', name: '多角度呈现图', desc: '展示侧面、背面及折叠等完整外观。', strategy: '三视图对齐，透视比例精准缩放。' },
  { id: 'ambient-scene', name: '场景氛围图', desc: '强光影写实渲染，增强商品的高级质感。', strategy: '暖色调逆光底板，配合微小阴影质感。' },
  { id: 'detail-zoom', name: '商品细节图', desc: '局部放大，精细展现材质和精湛工艺。', strategy: '中心放大镜切割圆圈，拉线批注。' },
  { id: 'brand-story', name: '品牌故事图', desc: '传达品牌匠心，突显高档商品格调。', strategy: '英文点缀，加宽留白，典雅无衬线排版。' },
  { id: 'specs-info', name: '尺寸/规格/容量图', desc: '直观标注物理尺寸与对比参照物。', strategy: '添加标注线与比例尺，数值一目了然。' },
  { id: 'contrast-effect', name: '效果对比图', desc: '使用前/后、升级前/后的直观效果。', strategy: '双栏垂直切割，BEFORE / AFTER 徽章强对抗。' },
  { id: 'tech-specs', name: '详细规格/参数表', desc: '将复杂工业数据整合为超清美化表格。', strategy: '圆角半透明卡片表格，结构化突出核心。' },
  { id: 'manufacturing', name: '工艺制作图', desc: '展示精密做工、材质层级拆解。', strategy: '爆炸视图效果，精细拆解元器件架构。' },
  { id: 'freebies', name: '配件/赠品图', desc: '明确告知用户收货拆箱的丰富组合。', strategy: '买即送角贴，配全套礼盒全家福。' },
  { id: 'series-show', name: '系列展示图', desc: '多配色、多SKU合辑呈现，极大提升加购。', strategy: '多色环绕渐变，卡片式并列。' },
  { id: 'ingredients', name: '商品成分图', desc: '透明呈现成分比例或纯净配料表。', strategy: '分子网格配图，科学健康风骨。' },
  { id: 'warranty', name: '售后保障图', desc: '官方质保、包邮无忧、金牌认证退换。', strategy: '醒目信任徽章，构建消费安全感。' },
  { id: 'usage-tips', name: '使用建议图', desc: '温馨提示使用建议、充电与养护说明。', strategy: '简洁图标列表，避免售后客诉纠纷。' },
]
