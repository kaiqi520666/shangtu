<script setup>
import { LoaderCircle, WandSparkles } from 'lucide-vue-next'
import GeneratorActionFooter from '@/components/GeneratorActionFooter.vue'
import GeneratorSidePanelShell from '@/components/GeneratorSidePanelShell.vue'
import OutfitPoseCard from '@/components/OutfitPoseCard.vue'

defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  poses: {
    type: Array,
    required: true,
  },
  selectedCount: {
    type: Number,
    default: 0,
  },
})

const emit = defineEmits(['back', 'generate-images', 'toggle-pose', 'update-pose'])
</script>

<template>
  <GeneratorSidePanelShell>
    <section class="space-y-4 p-5">
      <h3 class="text-xs font-bold text-slate-900">选择场景</h3>

      <div v-if="loading" class="flex h-80 items-center justify-center rounded-2xl bg-slate-100">
        <div class="space-y-3 text-center text-slate-400">
          <div class="flex justify-center gap-2">
            <span class="h-3 w-3 animate-pulse rounded-full bg-slate-400"></span>
            <span class="h-3 w-3 animate-pulse rounded-full bg-slate-400 delay-100"></span>
            <span class="h-3 w-3 animate-pulse rounded-full bg-slate-400 delay-200"></span>
          </div>
          <p class="text-xs font-medium">生成中...</p>
        </div>
      </div>

      <div v-else class="space-y-3">
        <OutfitPoseCard
          v-for="(pose, index) in poses"
          :key="pose.id"
          :pose="pose"
          :index="index"
          @toggle="emit('toggle-pose', $event)"
          @update="(...args) => emit('update-pose', ...args)"
        />
      </div>
    </section>

    <template #footer>
      <GeneratorActionFooter
        :primary-text="loading ? '请先等待场景生成' : `生成场景图片（${selectedCount}张）`"
        :primary-disabled="loading || selectedCount === 0"
        secondary-text="上一步"
        @secondary="emit('back')"
        @primary="emit('generate-images')"
      >
        <template #primary-icon>
          <LoaderCircle v-if="loading" class="h-4 w-4 animate-spin" />
          <WandSparkles v-else class="h-4 w-4" />
        </template>
      </GeneratorActionFooter>
    </template>
  </GeneratorSidePanelShell>
</template>
