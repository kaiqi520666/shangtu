import { reactive } from "vue";

import { getImageCapabilities } from "@/api/image.js";

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

const ratioOptionRegistry = {
  '1:1': { label: '1:1', description: '正方形' },
  '3:2': { label: '3:2', description: '横图' },
  '2:3': { label: '2:3', description: '竖图' },
  '4:3': { label: '4:3', description: '横图' },
  '3:4': { label: '3:4', description: '竖图' },
  '5:4': { label: '5:4', description: '横图' },
  '4:5': { label: '4:5', description: '竖图' },
  '16:9': { label: '16:9', description: '横图' },
  '9:16': { label: '9:16', description: '竖图' },
  '2:1': { label: '2:1', description: '横幅' },
  '1:2': { label: '1:2', description: '长竖图' },
  '21:9': { label: '21:9', description: '横图' },
  '9:21': { label: '9:21', description: '长竖图' },
}

const qualityOptionRegistry = {
  '1K': { title: '1K', subtitle: '更快' },
  '2K': { title: '2K', subtitle: '推荐' },
  '4K': { title: '4K', subtitle: '更精细' },
}

const qualityOrder = ['1K', '2K', '4K']

export const ratioOptions = reactive([])
export const qualityOptions = reactive([])

export const defaultImageCreditCosts = {
  '1K': 1,
  '2K': 2,
  '4K': 4,
}

export const resolutionMap = reactive({})

let imageCapabilitiesLoaded = false
let imageCapabilitiesPromise = null

function replaceReactiveArray(target, next) {
  target.splice(0, target.length, ...next)
}

function replaceReactiveMap(target, next) {
  Object.keys(target).forEach((key) => {
    delete target[key]
  })
  Object.entries(next).forEach(([key, value]) => {
    target[key] = value
  })
}

function sortQualities(qualities) {
  return [...qualities].sort((left, right) => {
    const leftIndex = qualityOrder.indexOf(left)
    const rightIndex = qualityOrder.indexOf(right)
    if (leftIndex === -1 && rightIndex === -1) return left.localeCompare(right)
    if (leftIndex === -1) return 1
    if (rightIndex === -1) return -1
    return leftIndex - rightIndex
  })
}

function buildRatioOptions(nextMap) {
  return Object.keys(nextMap).map((ratio) => {
    const meta = ratioOptionRegistry[ratio] || {}
    return {
      value: ratio,
      label: meta.label || ratio,
      description: meta.description || '',
    }
  })
}

function buildQualityOptions(nextMap) {
  const supported = new Set()
  Object.values(nextMap).forEach((qualityMap) => {
    Object.keys(qualityMap).forEach((quality) => supported.add(quality))
  })
  return sortQualities([...supported]).map((quality) => {
    const meta = qualityOptionRegistry[quality] || {}
    return {
      value: quality,
      title: meta.title || quality,
      subtitle: meta.subtitle || '',
    }
  })
}

function normalizeCapabilityMap(rawMap) {
  const nextMap = {}
  Object.entries(rawMap || {}).forEach(([ratio, qualities]) => {
    if (!qualities || typeof qualities !== 'object') return
    const normalizedQualities = {}
    Object.entries(qualities).forEach(([quality, dims]) => {
      if (!Array.isArray(dims) || dims.length < 2) return
      const width = Number(dims[0])
      const height = Number(dims[1])
      if (!Number.isFinite(width) || !Number.isFinite(height)) return
      normalizedQualities[normalizeImageQuality(quality)] = [width, height]
    })
    if (Object.keys(normalizedQualities).length > 0) {
      nextMap[ratio] = normalizedQualities
    }
  })
  return nextMap
}

export function applyImageCapabilities(rawMap) {
  const nextMap = normalizeCapabilityMap(rawMap)
  replaceReactiveMap(resolutionMap, nextMap)
  replaceReactiveArray(ratioOptions, buildRatioOptions(nextMap))
  replaceReactiveArray(qualityOptions, buildQualityOptions(nextMap))
}

export async function initImageCapabilities() {
  if (imageCapabilitiesLoaded) return
  if (!imageCapabilitiesPromise) {
    imageCapabilitiesPromise = (async () => {
      const result = await getImageCapabilities()
      if (result.code !== 0) {
        throw new Error(result.message || '图片能力加载失败')
      }
      applyImageCapabilities(result.data?.resolution_map || {})
      imageCapabilitiesLoaded = true
    })().catch((error) => {
      imageCapabilitiesPromise = null
      throw error
    })
  }
  return imageCapabilitiesPromise
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

export function normalizeImageQuality(quality) {
  return String(quality || '').replace(/\s+/g, '').toUpperCase()
}

export function getImageCreditCost(quality, costs = defaultImageCreditCosts) {
  const normalized = normalizeImageQuality(quality)
  const cost = Number(costs?.[normalized] ?? defaultImageCreditCosts[normalized])
  return Number.isFinite(cost) && cost > 0 ? cost : null
}

export function getImageBatchCreditCost({ quality = '1K', count = 1, costs } = {}) {
  const unitCost = getImageCreditCost(quality, costs)
  const imageCount = Math.max(0, Number(count || 0))
  if (!unitCost || !Number.isFinite(imageCount)) return null
  return unitCost * imageCount
}

export function formatImageLabel({ ratio = '1:1', quality = '1K' } = {}) {
  const ratioOption = ratioOptions.find((option) => option.value === ratio) || ratioOptions[0]
  const ratioValue = ratioOption?.value || ratio
  const ratioLabel = ratioOption?.label || ratio
  const effectiveQuality = resolveQuality(ratioValue, quality) || quality
  const dims = resolutionMap[ratioValue]?.[effectiveQuality]
  if (!dims) {
    return `${effectiveQuality} / ${ratioLabel}`
  }
  const [width, height] = dims
  return `${effectiveQuality} / ${ratioLabel} / ${width}x${height}`
}

export function createDefaultGenerationSettings(overrides = {}) {
  const defaultRatio = ratioOptions[0]?.value || '1:1'
  const baseRatio = overrides.ratio || defaultRatio
  const defaultQuality = resolveQuality(baseRatio, overrides.quality || '1K') || overrides.quality || '1K'
  return {
    platform: '亚马逊',
    language: '中文',
    ratio: baseRatio,
    quality: defaultQuality,
    productInput: '',
    ...overrides,
  }
}
