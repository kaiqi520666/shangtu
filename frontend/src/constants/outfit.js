export const outfitRatioOptions = [
  { value: '3:4', label: '3:4' },
  { value: '1:1', label: '1:1' },
  { value: '9:16', label: '9:16' },
]

export const outfitFrameOptions = [
  { value: '全身', label: '全身' },
  { value: '四分之三', label: '四分之三' },
  { value: '半身', label: '半身' },
  { value: '特写', label: '特写' },
]

export const outfitAngleOptions = [
  { value: '正面', label: '正面' },
  { value: '侧面', label: '侧面' },
  { value: '3/4侧', label: '3/4侧' },
  { value: '背面', label: '背面' },
]

export const modelLibrary = [
  {
    id: 'model-01',
    name: '清透自然女模',
    image: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=320&q=80',
  },
  {
    id: 'model-02',
    name: '都市短发女模',
    image: 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=320&q=80',
  },
  {
    id: 'model-03',
    name: '休闲男模',
    image: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=320&q=80',
  },
  {
    id: 'model-04',
    name: '欧美卷发女模',
    image: 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=320&q=80',
  },
  {
    id: 'model-05',
    name: '韩系长发女模',
    image: 'https://images.unsplash.com/photo-1524504388940-b1c1722653e1?auto=format&fit=crop&w=320&q=80',
  },
  {
    id: 'model-06',
    name: '金发男模',
    image: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?auto=format&fit=crop&w=320&q=80',
  },
]

export const scenePresets = [
  { id: 'studio', label: '纯色棚拍' },
  { id: 'street', label: '都市街头' },
  { id: 'cafe', label: '街角咖啡' },
  { id: 'lawn', label: '自然草坪' },
  { id: 'beach', label: '度假海滩' },
  { id: 'home', label: '温馨居家' },
  { id: 'gallery', label: '艺术展馆' },
]

export const outfitPoseTemplates = [
  {
    id: 'pose-stand-front',
    text: '自然站立，双手垂在身侧，直视镜头，放松展示毛衣整体版型',
    frame: '全身',
    angle: '正面',
  },
  {
    id: 'pose-pocket-side',
    text: '身体微侧，一只手插牛仔裤口袋，另一只手轻抓袖口看向镜头',
    frame: '四分之三',
    angle: '3/4侧',
  },
  {
    id: 'pose-detail-collar',
    text: '微微抬手整理毛衣领口，身体稍前倾，表情柔和展示领口细节',
    frame: '四分之三',
    angle: '正面',
  },
  {
    id: 'pose-walk-back',
    text: '脚步微错开站立，双手向后轻拢头发，展示毛衣落肩版型',
    frame: '全身',
    angle: '3/4侧',
  },
]

export const outfitPreviewSlides = [
  {
    caption: '多场景自由切换，轻松拍出大片氛围。',
    sourceImage: 'https://images.unsplash.com/photo-1525507119028-ed4c629a60a3?auto=format&fit=crop&w=360&q=80',
    resultImages: [
      'https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=420&q=80',
      'https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?auto=format&fit=crop&w=420&q=80',
      'https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?auto=format&fit=crop&w=420&q=80',
    ],
  },
  {
    caption: '同场景多姿势，一键解锁整套实拍图。',
    sourceImage: 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=360&q=80',
    resultImages: [
      'https://images.unsplash.com/photo-1485968579580-b6d095142e6e?auto=format&fit=crop&w=420&q=80',
      'https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=420&q=80',
      'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=420&q=80',
    ],
  },
]

export const outfitResultImages = [
  'https://images.unsplash.com/photo-1509631179647-0177331693ae?auto=format&fit=crop&w=900&q=80',
  'https://images.unsplash.com/photo-1496747611176-843222e1e57c?auto=format&fit=crop&w=900&q=80',
  'https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?auto=format&fit=crop&w=900&q=80',
  'https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=900&q=80',
]
