<script setup>
import { watch } from 'vue'
import ImageQualitySelector from '@/components/generation/image/ImageQualitySelector.vue'
import AiAssistedTextarea from '@/components/generation/workspace/AiAssistedTextarea.vue'
import GeneratorPanelSection from '@/components/generation/workspace/GeneratorPanelSection.vue'
import AppSelect from '@/components/ui/AppSelect.vue'
import {
  languageOptions,
  platformOptions,
  ratioOptions,
  resolveQuality,
} from '@/constants/generator.js'

const props = defineProps({
  settings: {
    type: Object,
    required: true,
  },
  selectedImageLabel: {
    type: String,
    required: true,
  },
  generateSellingPoints: {
    type: Function,
    default: null,
  },
  showProductInput: {
    type: Boolean,
    default: true,
  },
  showAiWrite: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['update:settings'])

watch(
  () => props.settings.ratio,
  (ratio) => {
    const next = resolveQuality(ratio, props.settings.quality)
    if (next && next !== props.settings.quality) {
      updateSetting('quality', next)
    }
  },
)

function updateSetting(key, value) {
  emit('update:settings', {
    ...props.settings,
    [key]: value,
  })
}
</script>

<template>
  <GeneratorPanelSection title="生成设置">
    <div>
      <label class="mb-1.5 block text-xs font-bold text-slate-500">投放平台</label>
      <AppSelect
        :model-value="settings.platform"
        :options="platformOptions"
        @update:model-value="updateSetting('platform', $event)"
      />
    </div>

    <div class="grid grid-cols-2 gap-3.5">
      <div>
        <label class="mb-1.5 block text-xs font-bold text-slate-500">排版语言</label>
        <AppSelect
          :model-value="settings.language"
          :options="languageOptions"
          @update:model-value="updateSetting('language', $event)"
        />
      </div>
      <div>
        <label class="mb-1.5 block text-xs font-bold text-slate-500">图片比例</label>
        <AppSelect
          :model-value="settings.ratio"
          :options="ratioOptions"
          @update:model-value="updateSetting('ratio', $event)"
        />
      </div>
    </div>

    <ImageQualitySelector
      :model-value="settings.quality"
      :ratio="settings.ratio"
      :output-label="selectedImageLabel"
      @update:model-value="updateSetting('quality', $event)"
    />

    <div v-if="showProductInput">
      <AiAssistedTextarea
        v-if="showAiWrite"
        :model-value="settings.productInput"
        label="商品卖点&要求"
        action-label="AI 帮写"
        loading-label="AI 帮写中..."
        :rows="6"
        :generate-draft="generateSellingPoints"
        placeholder="建议包含以下信息生成更精准：&#10;1.产品名称&#10;2.核心卖点&#10;3.适用人群&#10;4.期望场景&#10;5.具体参数"
        @update:model-value="updateSetting('productInput', $event)"
      />
      <textarea
        v-else
        :value="settings.productInput"
        data-testid="product-input"
        class="h-32 w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-800 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:ring-1 focus:ring-primary"
        placeholder="建议包含以下信息生成更精准：
1.产品名称
2.核心卖点
3.适用人群
4.期望场景
5.具体参数"
        @input="updateSetting('productInput', $event.target.value)"
      ></textarea>
    </div>
  </GeneratorPanelSection>
</template>
