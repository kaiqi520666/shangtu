import { computed, reactive, ref } from 'vue'
import { ratioOptions, resolutionMap } from '@/constants/generator.js'
import { suiteStructureDefaults } from '@/constants/productSuite.js'
import { useToast } from '@/composables/useToast.js'

const THEME_COLORS = {
  primary: '#10b981',
  primaryDark: '#059669',
  secondary: '#14b8a6',
  slate900: '#0f172a',
  slate700: '#334155',
  slate500: '#64748b',
  slate100: '#f1f5f9',
}

export function useProductSuiteGenerator() {
  const toast = useToast()
  const uploadedImages = ref([])
  const mainImageIndex = ref(0)
  const aiLoading = ref(false)
  const generating = ref(false)
  const generatedCount = ref(0)
  const genLogs = ref([])
  const outputCards = ref([])
  const zoomCard = ref(null)
  const currentTaskTitle = ref(`Suite_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}_商品套图`)

  const settings = reactive({
    platform: '亚马逊',
    language: '中文',
    ratio: '1:1',
    quality: '1K',
    productInput: '',
  })

  // TODO: replace with API
  const suiteStructure = ref(
    suiteStructureDefaults.map((item) => ({
      ...item,
      enabled: true,
      count: item.defaultCount,
    })),
  )

  const totalCount = computed(() =>
    suiteStructure.value.reduce((sum, item) => {
      if (!item.enabled) return sum
      return sum + item.count
    }, 0),
  )
  const hasGenerationSource = computed(
    () => uploadedImages.value.length > 0 && settings.productInput.trim().length > 0,
  )
  const canGenerate = computed(() => hasGenerationSource.value && totalCount.value > 0 && !generating.value)
  const selectedCards = computed(() => outputCards.value.filter((card) => card.selected))
  const selectedCardsCount = computed(() => selectedCards.value.length)
  const selectedRatioOption = computed(
    () => ratioOptions.find((option) => option.value === settings.ratio) || ratioOptions[0],
  )
  const selectedImageLabel = computed(() => {
    const { width, height } = getCardSize()
    return `${settings.quality} / ${selectedRatioOption.value.label} / ${width}x${height}`
  })

  async function generateSellingPointsWithAI() {
    const textInput = settings.productInput.trim()
    if (!textInput && uploadedImages.value.length === 0) {
      toast.info('请先上传商品图或输入商品名称，AI 才能帮写卖点')
      return ''
    }

    aiLoading.value = true
    await wait(450)
    // TODO: replace with API
    const queryName =
      textInput
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean)[0] || '上传商品图'

    aiLoading.value = false
    return `${queryName}
1. 清晰展示商品主体，适配平台首图规范
2. 提炼核心卖点，统一套图视觉风格
3. 兼顾场景、细节与信任背书，提高转化效率`
  }

  async function generateSuiteImages() {
    if (uploadedImages.value.length === 0) {
      toast.info('请先上传商品图片')
      return
    }

    if (!settings.productInput.trim()) {
      toast.info('请填写商品卖点与要求')
      return
    }

    const queue = buildSuiteQueue()
    if (queue.length === 0) {
      toast.info('请至少选择一个套图类型')
      return
    }

    generating.value = true
    generatedCount.value = 0
    genLogs.value = ['商品套图生成任务初始化...', '读取商品图片、平台规范与套图结构...']
    outputCards.value = []

    const mainImg = uploadedImages.value[mainImageIndex.value]
    for (const item of queue) {
      await wait(180)
      genLogs.value.push(`正在生成 [${item.name}] 第 ${item.index} 张视觉图...`)
      const dataUrl = await renderSuiteImage(item, mainImg)
      outputCards.value.push({
        id: makeId(),
        typeId: item.id,
        dataUrl,
        selected: true,
        strategyTitle: `${item.name} ${item.index}`,
        strategyContent: item.description,
      })
      generatedCount.value += 1
    }

    genLogs.value.push('商品套图已生成完成，可继续预览、下载或重算单张。')
    generating.value = false
    toast.success('商品套图已生成')
  }

  function buildSuiteQueue() {
    return suiteStructure.value.flatMap((item) => {
      if (!item.enabled) return []
      return Array.from({ length: item.count }, (_, index) => ({
        id: item.id,
        name: item.name,
        description: item.description,
        index: index + 1,
      }))
    })
  }

  function getCardSize() {
    const [width, height] = resolutionMap[settings.quality]?.[settings.ratio] || resolutionMap['1K']['1:1']
    return { width, height }
  }

  function renderSuiteImage(item, productImgSrc) {
    return new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      const { width, height } = getCardSize()

      canvas.width = width
      canvas.height = height
      paintSuiteBackground(ctx, width, height, item)

      const img = new window.Image()
      img.onload = () => {
        paintProduct(ctx, img, width, height, item)
        paintSuiteCopy(ctx, width, height, item)
        resolve(canvas.toDataURL('image/png'))
      }
      img.onerror = reject
      img.src = productImgSrc
    })
  }

  function paintSuiteBackground(ctx, width, height, item) {
    const gradient = ctx.createLinearGradient(0, 0, width, height)
    if (item.id === 'white-bg') {
      gradient.addColorStop(0, '#ffffff')
      gradient.addColorStop(1, '#f8fafc')
    } else if (item.id === 'scene') {
      gradient.addColorStop(0, '#ecfdf5')
      gradient.addColorStop(1, '#f8fafc')
    } else if (item.id === 'selling-point') {
      gradient.addColorStop(0, '#f0fdfa')
      gradient.addColorStop(1, '#ffffff')
    } else {
      gradient.addColorStop(0, '#f8fafc')
      gradient.addColorStop(1, '#e2e8f0')
    }

    ctx.fillStyle = gradient
    ctx.fillRect(0, 0, width, height)
    ctx.strokeStyle = 'rgba(16, 185, 129, 0.08)'
    ctx.lineWidth = 1
    for (let x = 0; x < width; x += 48) {
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, height)
      ctx.stroke()
    }
  }

  function paintProduct(ctx, img, width, height, item) {
    const isInfoLayout = item.id === 'selling-point' || item.id === 'detail'
    const productX = isInfoLayout ? width * 0.68 : width * 0.5
    const productY = isInfoLayout ? height * 0.58 : height * 0.54
    const productW = width * (isInfoLayout ? 0.42 : 0.58)
    const productH = height * (isInfoLayout ? 0.5 : 0.6)

    ctx.shadowColor = 'rgba(15, 23, 42, 0.12)'
    ctx.shadowBlur = 30
    ctx.shadowOffsetY = 16
    ctx.drawImage(img, productX - productW / 2, productY - productH / 2, productW, productH)
    ctx.shadowColor = 'transparent'
    ctx.shadowBlur = 0
    ctx.shadowOffsetY = 0
  }

  function paintSuiteCopy(ctx, width, height, item) {
    const productName = getProductNameFromInput(settings.productInput)
    const titleMap = {
      'white-bg': `${productName} 官方标准白底图`,
      scene: `${productName} 高转化使用场景`,
      'selling-point': `${productName} 核心卖点拆解`,
      detail: `${productName} 精细材质细节`,
    }
    const lines = getCopyLines(item)

    ctx.fillStyle = 'rgba(255,255,255,0.92)'
    ctx.beginPath()
    ctx.roundRect(width * 0.06, height * 0.07, width * 0.43, height * 0.34, 18)
    ctx.fill()
    ctx.strokeStyle = 'rgba(16, 185, 129, 0.18)'
    ctx.stroke()

    ctx.fillStyle = THEME_COLORS.primary
    ctx.beginPath()
    ctx.roundRect(width * 0.085, height * 0.105, 122, 30, 8)
    ctx.fill()
    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 14px "Noto Sans SC", sans-serif'
    ctx.fillText('NodePass AI', width * 0.105, height * 0.105 + 20)

    ctx.fillStyle = THEME_COLORS.slate900
    ctx.font = 'bold 30px "Noto Sans SC", sans-serif'
    ctx.fillText(titleMap[item.id] || item.name, width * 0.085, height * 0.105 + 72)

    let lineY = height * 0.105 + 118
    lines.forEach((line, index) => {
      ctx.fillStyle = THEME_COLORS.primaryDark
      ctx.beginPath()
      ctx.arc(width * 0.095, lineY - 5, 9, 0, Math.PI * 2)
      ctx.fill()
      ctx.fillStyle = '#ffffff'
      ctx.font = 'bold 11px "Plus Jakarta Sans", sans-serif'
      ctx.fillText(index + 1, width * 0.091, lineY - 1)
      ctx.fillStyle = THEME_COLORS.slate700
      ctx.font = '15px "Noto Sans SC", sans-serif'
      ctx.fillText(line, width * 0.12, lineY)
      lineY += 38
    })

    ctx.fillStyle = THEME_COLORS.slate100
    ctx.beginPath()
    ctx.roundRect(width - 190, 24, 164, 30, 7)
    ctx.fill()
    ctx.fillStyle = THEME_COLORS.slate700
    ctx.font = 'bold 12px "Noto Sans SC", sans-serif'
    ctx.fillText(`${settings.platform} / ${settings.language}`, width - 176, 44)
  }

  function getCopyLines(item) {
    const map = {
      'white-bg': ['平台规范首图', '主体清晰突出', '减少干扰元素'],
      scene: ['真实使用场景', '提升购买代入', '强化生活质感'],
      'selling-point': ['三段式卖点表达', '重点参数可视化', '信息层级清晰'],
      detail: ['局部细节放大', '材质工艺说明', '降低售前疑虑'],
    }
    return map[item.id] || ['统一视觉风格', '适配多平台规范', '提升商品转化']
  }

  function getStructureName(id) {
    return suiteStructureDefaults.find((item) => item.id === id)?.name || id
  }

  function getStructureStrategy(id) {
    return suiteStructureDefaults.find((item) => item.id === id)?.description || '商品套图生成'
  }

  function toggleCardSelection(id) {
    const card = outputCards.value.find((item) => item.id === id)
    if (card) card.selected = !card.selected
  }

  function toggleSelectAllCards(value) {
    outputCards.value.forEach((card) => {
      card.selected = value
    })
  }

  function batchDownload() {
    if (selectedCards.value.length === 0) {
      toast.info('请先勾选需要下载的套图')
      return
    }

    selectedCards.value.forEach((card, index) => {
      window.setTimeout(() => {
        downloadSingleImage(card)
      }, index * 150)
    })
  }

  function downloadSingleImage(card) {
    const link = document.createElement('a')
    link.href = card.dataUrl
    link.download = `${currentTaskTitle.value}_${card.strategyTitle || getStructureName(card.typeId)}.png`
    link.click()
  }

  async function regenerateSingleCard(card) {
    if (uploadedImages.value.length === 0) {
      toast.info('请先上传商品图片')
      return
    }

    const mainImg = uploadedImages.value[mainImageIndex.value]
    const suiteItem = suiteStructureDefaults.find((item) => item.id === card.typeId)
    card.dataUrl = await renderSuiteImage(
      {
        id: card.typeId,
        name: suiteItem?.name || card.strategyTitle || '商品套图',
        description: suiteItem?.description || card.strategyContent || '商品套图生成',
        index: 1,
      },
      mainImg,
    )
    toast.success('该套图已重新生成')
  }

  return {
    uploadedImages,
    mainImageIndex,
    aiLoading,
    generating,
    generatedCount,
    genLogs,
    outputCards,
    zoomCard,
    currentTaskTitle,
    settings,
    suiteStructure,
    totalCount,
    hasGenerationSource,
    canGenerate,
    selectedCards,
    selectedCardsCount,
    selectedImageLabel,
    generateSellingPointsWithAI,
    generateSuiteImages,
    showNotice: toast.info,
    getStructureName,
    getStructureStrategy,
    toggleCardSelection,
    toggleSelectAllCards,
    batchDownload,
    downloadSingleImage,
    regenerateSingleCard,
  }
}

function wait(ms) {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

function makeId() {
  return `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

function getProductNameFromInput(input) {
  return (
    input
      .split('\n')
      .map((line) => line.trim())
      .filter(Boolean)[0] || '当前商品'
  )
}
