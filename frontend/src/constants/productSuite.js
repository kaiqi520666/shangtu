export const suiteStructureDefaults = [
  {
    id: 'white-bg',
    name: '白底图',
    description: '适配平台首图规范，突出商品主体与干净轮廓。',
    defaultCount: 1,
    maxCount: 3,
  },
  {
    id: 'scene',
    name: '场景图',
    description: '把商品放进真实使用环境，强化购买代入感。',
    defaultCount: 2,
    maxCount: 6,
  },
  {
    id: 'selling-point',
    name: '卖点图',
    description: '提炼核心优势，用高可读信息块表达产品价值。',
    defaultCount: 2,
    maxCount: 6,
  },
  {
    id: 'detail',
    name: '细节图',
    description: '展示材质、结构、功能细节，降低用户决策疑虑。',
    defaultCount: 2,
    maxCount: 6,
  },
]

export const productSuitePreviewSlides = [
  {
    caption: '围绕同一商品自动生成白底、场景、卖点和细节套图，适合多平台批量上架。',
    sourceImage:
      'https://images.unsplash.com/photo-1585386959984-a41552231658?auto=format&fit=crop&w=360&q=80',
    resultImages: [
      'https://images.unsplash.com/photo-1586495777744-4413f21062fa?auto=format&fit=crop&w=420&q=80',
      'https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=420&q=80',
      'https://images.unsplash.com/photo-1612817288484-6f916006741a?auto=format&fit=crop&w=420&q=80',
    ],
  },
  {
    caption: '统一画面风格与信息密度，让商品套图从主图到详情图保持完整视觉体系。',
    sourceImage:
      'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=360&q=80',
    resultImages: [
      'https://images.unsplash.com/photo-1549298916-b41d501d3772?auto=format&fit=crop&w=420&q=80',
      'https://images.unsplash.com/photo-1608231387042-66d1773070a5?auto=format&fit=crop&w=420&q=80',
      'https://images.unsplash.com/photo-1600185365483-26d7a4cc7519?auto=format&fit=crop&w=420&q=80',
    ],
  },
]
