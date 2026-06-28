<script setup>
import { computed, ref, watch } from 'vue'
import { Trash2 } from 'lucide-vue-next'
import AppModal from '@/components/ui/AppModal.vue'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  card: {
    type: Object,
    default: null,
  },
  moduleName: {
    type: String,
    default: '',
  },
  submitting: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'submit', 'delete'])

const draftPrompt = ref('')

const canSubmit = computed(() => draftPrompt.value.trim().length > 0)

watch(
  () => [props.open, props.card?.taskId, props.card?.userPrompt],
  () => {
    if (props.open && props.card) {
      draftPrompt.value = props.card.userPrompt || props.card.strategyContent || ''
    }
  },
  { immediate: true },
)

function handleSubmit() {
  const userPrompt = draftPrompt.value.trim()
  if (!userPrompt) return
  emit('submit', userPrompt)
}
</script>

<template>
  <AppModal
    :open="open"
    title="编辑图片"
    panel-class="w-full max-w-lg"
    @close="emit('close')"
  >
    <div v-if="card" class="space-y-4 p-5">
      <div class="overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
        <img :src="card.dataUrl" class="mx-auto max-h-56 object-contain" referrerpolicy="no-referrer" alt="当前图片" />
      </div>
      <div class="flex items-center gap-2 text-xs text-slate-600">
        <span class="rounded-full bg-slate-100 px-2 py-0.5 font-semibold">{{ moduleName }}</span>
        <span class="text-slate-400">{{ card.strategyTitle }}</span>
      </div>
      <div>
        <label class="mb-1.5 block text-xs font-semibold text-slate-700">用户提示词</label>
        <textarea
          v-model="draftPrompt"
          rows="8"
          class="w-full resize-none rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs leading-5 text-slate-800 placeholder:text-slate-400 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary/30"
          placeholder="描述这张图希望如何生成，例如背景、构图、信息层级、视觉重点。"
        />
      </div>
      <div class="flex items-center justify-between border-t border-slate-100 pt-4">
        <button
          type="button"
          class="flex items-center gap-1 text-xs font-semibold text-rose-500 hover:text-rose-600"
          @click="emit('delete')"
        >
          <Trash2 class="h-3.5 w-3.5" />
          删除图片
        </button>
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="rounded-lg border border-slate-200 px-3.5 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50"
            @click="emit('close')"
          >
            取消
          </button>
          <button
            type="button"
            class="rounded-lg bg-primary px-3.5 py-2 text-xs font-bold text-white shadow-sm hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="submitting || !canSubmit"
            @click="handleSubmit"
          >
            {{ submitting ? '提交中...' : '重新生成' }}
          </button>
        </div>
      </div>
    </div>
  </AppModal>
</template>
