import { computed, reactive, ref } from 'vue'
import {
  modelLibrary,
  outfitPoseTemplates,
  outfitPreviewSlides,
  outfitResultImages,
  scenePresets,
} from '@/constants/outfit.js'
import { useToast } from '@/composables/useToast.js'

export function useOutfitGenerator() {
  const toast = useToast()
  const garmentImages = ref([])
  const mainGarmentIndex = ref(0)
  const selectedModelId = ref(modelLibrary[0]?.id || '')
  const selectedScenes = ref(['street'])
  const sceneDescription = ref('')
  const ratio = ref('3:4')
  const workflowStep = ref('config')
  const loadingScenes = ref(false)
  const generating = ref(false)
  const generatedCount = ref(0)
  const recommendedPoses = ref([])
  const outputCards = ref([])
  const zoomCard = ref(null)
  const genLogs = ref([])
  const currentTaskTitle = ref(`Outfit_${new Date().toISOString().slice(0, 10).replace(/-/g, '')}_服饰穿搭`)

  const settings = reactive({
    platform: '服饰穿搭',
    language: '中文',
  })

  const selectedModel = computed(() => modelLibrary.find((model) => model.id === selectedModelId.value))
  const canGenerateScenes = computed(() => garmentImages.value.length > 0 && Boolean(selectedModelId.value))
  const selectedPoseCount = computed(() => recommendedPoses.value.filter((pose) => pose.selected).length)
  const selectedCards = computed(() => outputCards.value.filter((card) => card.selected))
  const selectedCardsCount = computed(() => selectedCards.value.length)
  const selectedImageLabel = computed(() => `${ratio.value} / Mock`)
  const previewSlides = computed(() => {
    const uploadedImage = garmentImages.value[mainGarmentIndex.value]
    if (!uploadedImage) return outfitPreviewSlides
    return outfitPreviewSlides.map((slide) => ({
      ...slide,
      sourceImage: uploadedImage,
    }))
  })

  async function generateRecommendedScenes() {
    if (!canGenerateScenes.value) {
      toast.info('请先上传服装图片并选择模特')
      return
    }

    loadingScenes.value = true
    workflowStep.value = 'scene-loading'
    await wait(700)

    // TODO: replace with API
    const sceneNames = selectedScenes.value.length
      ? selectedScenes.value.map((id) => scenePresets.find((scene) => scene.id === id)?.label).filter(Boolean)
      : [sceneDescription.value.trim() || '自定义场景']

    recommendedPoses.value = outfitPoseTemplates.map((pose, index) => ({
      ...pose,
      id: `${pose.id}-${index}`,
      sceneName: sceneNames[index % sceneNames.length] || '推荐场景',
      selected: true,
    }))

    loadingScenes.value = false
    workflowStep.value = 'scene-review'
  }

  function updatePose(index, patch) {
    const current = recommendedPoses.value[index]
    if (!current) return
    recommendedPoses.value[index] = {
      ...current,
      ...patch,
    }
  }

  function togglePose(index) {
    const current = recommendedPoses.value[index]
    if (!current) return
    updatePose(index, { selected: !current.selected })
  }

  async function generateOutfitImages() {
    const selectedPoses = recommendedPoses.value.filter((pose) => pose.selected)
    if (selectedPoses.length === 0) {
      toast.info('请至少选择一个推荐姿势')
      return
    }

    generating.value = true
    workflowStep.value = 'generating'
    generatedCount.value = 0
    outputCards.value = []
    genLogs.value = ['服饰穿搭生成任务初始化...', '读取服装图、模特与场景设定...']

    for (const pose of selectedPoses) {
      await wait(220)
      genLogs.value.push(`正在生成 [${pose.sceneName}] ${pose.frame} / ${pose.angle} 穿搭图...`)
      outputCards.value.push({
        id: makeId(),
        typeId: pose.id,
        dataUrl: outfitResultImages[outputCards.value.length % outfitResultImages.length],
        selected: true,
        strategyTitle: pose.sceneName,
        strategyContent: `${pose.text}｜${pose.frame}｜${pose.angle}`,
      })
      generatedCount.value += 1
    }

    generating.value = false
    workflowStep.value = 'result'
    toast.success('服饰穿搭图片已生成')
  }

  function backToConfig() {
    workflowStep.value = 'config'
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

  function downloadSingleImage(card) {
    const link = document.createElement('a')
    link.href = card.dataUrl
    link.download = `${currentTaskTitle.value}_${card.strategyTitle || '服饰穿搭图'}.jpg`
    link.click()
  }

  function regenerateSingleCard(card) {
    card.dataUrl = outfitResultImages[Math.floor(Math.random() * outfitResultImages.length)]
    toast.success('该穿搭图已重新生成')
  }

  function getPoseName(id) {
    return recommendedPoses.value.find((pose) => pose.id === id)?.sceneName || '服饰穿搭图'
  }

  function getPoseStrategy(id) {
    return recommendedPoses.value.find((pose) => pose.id === id)?.text || '服饰穿搭场景生成'
  }

  return {
    garmentImages,
    mainGarmentIndex,
    selectedModelId,
    selectedScenes,
    sceneDescription,
    ratio,
    workflowStep,
    loadingScenes,
    generating,
    generatedCount,
    recommendedPoses,
    outputCards,
    zoomCard,
    genLogs,
    currentTaskTitle,
    settings,
    selectedModel,
    canGenerateScenes,
    selectedPoseCount,
    selectedCards,
    selectedCardsCount,
    selectedImageLabel,
    previewSlides,
    showNotice: toast.info,
    generateRecommendedScenes,
    updatePose,
    togglePose,
    generateOutfitImages,
    backToConfig,
    toggleCardSelection,
    toggleSelectAllCards,
    downloadSingleImage,
    regenerateSingleCard,
    getPoseName,
    getPoseStrategy,
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
