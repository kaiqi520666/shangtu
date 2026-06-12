<script setup>
import { computed, ref, watch } from 'vue'
import { HelpCircle, LoaderCircle, Sparkles, X } from 'lucide-vue-next'
import AppSelect from '@/components/ui/AppSelect.vue'
import {
  isQualitySupported,
  languageOptions,
  platformOptions,
  qualityOptions,
  ratioOptions,
  resolveQuality,
} from '@/constants/generator.js'

const props = defineProps({
  settings: {
    type: Object,
    required: true,
  },
  aiLoading: {
    type: Boolean,
    default: false,
  },
  selectedImageLabel: {
    type: String,
    required: true,
  },
  generateSellingPoints: {
    type: Function,
    required: true,
  },
})

const emit = defineEmits(['update:settings'])

const showAiPopover = ref(false)
const aiDraft = ref('')

const hasAiDraft = computed(() => aiDraft.value.trim().length > 0)

const isQualityEnabled = (quality) => isQualitySupported(props.settings.ratio, quality)

watch(
  () => props.settings.ratio,
  (ratio) => {
    const next = resolveQuality(ratio, props.settings.quality)
    if (next && next !== props.settings.quality) {
      updateSetting('quality', next)
    }
  },
)

async function handleAiWrite() {
  const draft = await props.generateSellingPoints()
  if (!draft) return
  aiDraft.value = draft
  showAiPopover.value = true
}

function confirmAiDraft() {
  if (!hasAiDraft.value) return
  updateSetting('productInput', aiDraft.value)
  showAiPopover.value = false
}

function selectQuality(quality) {
  if (!isQualityEnabled(quality)) return
  updateSetting('quality', quality)
}

function updateSetting(key, value) {
  emit('update:settings', {
    ...props.settings,
    [key]: value,
  })
}
</script>

<template>
  <div class="space-y-4 border-b border-slate-100 p-5">
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

    <div>
      <label class="mb-1.5 block text-xs font-bold text-slate-500">图片质量</label>
      <div class="grid grid-cols-3 gap-2">
        <button
          v-for="quality in qualityOptions"
          :key="quality.value"
          type="button"
          :disabled="!isQualityEnabled(quality.value)"
          class="rounded-lg border px-3 py-2 text-center transition-all"
          :class="
            !isQualityEnabled(quality.value)
              ? 'cursor-not-allowed border-slate-200 bg-slate-100 text-slate-300'
              : settings.quality === quality.value
                ? 'border-primary bg-primary/10 text-primary shadow-sm'
                : 'border-slate-200 bg-white text-slate-500 hover:border-slate-300 hover:bg-slate-50'
          "
          @click="selectQuality(quality.value)"
        >
          <span class="block text-sm font-bold leading-tight">{{ quality.title }}</span>
          <span
            class="mt-0.5 block text-xs leading-tight"
            :class="
              !isQualityEnabled(quality.value)
                ? 'text-slate-300'
                : settings.quality === quality.value
                  ? 'text-primary'
                  : 'text-slate-400'
            "
          >
            {{ isQualityEnabled(quality.value) ? quality.subtitle : '不支持' }}
          </span>
        </button>
      </div>
      <p class="mt-2 text-xs text-slate-400">当前输出：{{ selectedImageLabel }}</p>
    </div>

    <div>
      <div class="relative mb-1.5 flex items-center justify-between">
        <label class="flex items-center gap-1 text-xs font-bold text-slate-800">
          商品卖点&要求
          <HelpCircle class="h-3.5 w-3.5 text-slate-400" />
        </label>
        <button
          type="button"
          data-testid="ai-write-button"
          class="flex cursor-pointer items-center gap-1 rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-primary shadow-sm transition-colors hover:border-primary/30 hover:bg-primary/5 disabled:opacity-50"
          :disabled="aiLoading"
          @click="handleAiWrite"
        >
          <LoaderCircle v-if="aiLoading" class="h-3.5 w-3.5 animate-spin" />
          <Sparkles v-else class="h-3.5 w-3.5" />
          {{ aiLoading ? 'AI 帮写中...' : 'AI 帮写' }}
        </button>

        <div
          v-if="showAiPopover"
          class="absolute right-0 top-9 z-50 w-72 rounded-2xl border border-primary/20 bg-white p-3 shadow-xl shadow-primary/10"
        >
          <div class="mb-2.5 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Sparkles class="h-3.5 w-3.5" />
              </span>
              <div>
                <h4 class="text-xs font-bold text-slate-800">AI 帮写</h4>
                <p class="text-xs text-slate-400">可编辑后确认写入</p>
              </div>
            </div>
            <button
              type="button"
              class="rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600"
              @click="showAiPopover = false"
            >
              <X class="h-4 w-4" />
            </button>
          </div>
          <textarea
            v-model="aiDraft"
            class="h-36 w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-5 text-slate-700 outline-none transition-colors focus:border-primary focus:bg-white focus:ring-1 focus:ring-primary"
          ></textarea>
          <div class="mt-3 grid grid-cols-2 gap-2">
            <button
              type="button"
              class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-600 transition-colors hover:border-primary/30 hover:bg-primary/5 hover:text-primary"
              @click="handleAiWrite"
            >
              重新帮写
            </button>
            <button
              type="button"
              class="rounded-xl bg-primary px-3 py-2 text-xs font-semibold text-white shadow-md shadow-primary/20 transition-colors hover:bg-secondary"
              @click="confirmAiDraft"
            >
              确认
            </button>
          </div>
        </div>
      </div>
      <textarea
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
  </div>
</template>
