import {
  AudioLines,
  Boxes,
  Clapperboard,
  ImagePlus,
  Languages,
  Layers3,
  PlayCircle,
  Shirt,
  Sparkles,
  UserRound,
  WandSparkles,
  Workflow,
} from 'lucide-vue-next'
import avatar from '@/assets/home/avatar.jpg'
import detail from '@/assets/home/detail.jpg'
import hero from '@/assets/home/hero.jpg'
import outfit from '@/assets/home/outfit.jpg'
import suite from '@/assets/home/suite.jpg'
import video from '@/assets/home/video.jpg'
import voiceover from '@/assets/generator-previews/voiceover.webp'

export const homeImages = { avatar, detail, hero, outfit, suite, video }

export const featureItems = [
  {
    icon: Layers3,
    title: '商品套图',
    desc: '批量生成主图、场景图、卖点图和细节图。',
    to: '/generator/product-suite',
    image: suite,
  },
  {
    icon: ImagePlus,
    title: '商品详情图',
    desc: '根据卖点生成详情页模块图。',
    to: '/generator/product-image',
    image: detail,
  },
  {
    icon: Clapperboard,
    title: '商品视频',
    desc: '生成 UGC 种草、产品演示和广告短片。',
    to: '/generator/product-video',
    image: video,
  },
  {
    icon: Shirt,
    title: '服饰穿搭',
    desc: '上传服装图，搭配模特和拍摄场景。',
    to: '/generator/outfit',
    image: outfit,
  },
  {
    icon: Sparkles,
    title: '自由生图',
    desc: '支持文生图和多参考图生图。',
    to: '/generator/free-image',
    image: detail,
  },
  {
    icon: PlayCircle,
    title: '自由生视频',
    desc: '用提示词、参考图、视频和音频生成短片。',
    to: '/generator/free-video',
    image: video,
  },
  {
    icon: UserRound,
    title: '数字人',
    desc: '创建数字人口播和产品讲解视频。',
    to: '/generator/digital-human',
    image: avatar,
  },
  {
    icon: Languages,
    title: '视频翻译',
    desc: '将视频翻译为多语言版本。',
    to: '/generator/video-translation',
    image: avatar,
  },
  {
    icon: AudioLines,
    title: 'AI 配音',
    desc: '将文本生成自然流畅的 MP3 配音。',
    to: '/generator/voiceover',
    image: voiceover,
  },
]

export const workflowItems = [
  { icon: ImagePlus, title: '上传素材', desc: '图片、视频、音频统一进入素材池。' },
  { icon: Workflow, title: '选择场景', desc: '套图、详情、视频、数字人流程直达。' },
  { icon: WandSparkles, title: 'AI 生成', desc: '策略、提示词和参考素材协同生成。' },
  { icon: Boxes, title: '沉淀资产', desc: '结果自动进入资产库，方便复用下载。' },
]

export const showcaseItems = [
  { title: '图片内容', desc: '商品套图、详情图、自由生图', image: suite },
  { title: '服饰内容', desc: '模特穿搭、场景拍摄、比例适配', image: outfit },
  { title: '视频内容', desc: '商品视频、自由生视频、短片封面', image: video },
  {
    title: '从声音到多语言视频',
    desc: 'AI 配音生成自然语音，数字人完成口播表达，视频翻译拓展全球市场。',
    image: voiceover,
    actions: [
      { icon: AudioLines, title: 'AI 配音', to: '/generator/voiceover' },
      { icon: UserRound, title: '数字人', to: '/generator/digital-human' },
      { icon: Languages, title: '视频翻译', to: '/generator/video-translation' },
    ],
  },
]
