<script setup>
import StrategyReviewShell from "@/components/generation/StrategyReviewShell.vue";
import VideoStrategyCard from "@/components/product-video/VideoStrategyCard.vue";

const props = defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  brief: {
    type: String,
    default: "",
  },
  items: {
    type: Array,
    required: true,
  },
  metaText: {
    type: String,
    default: "",
  },
  dirty: {
    type: Boolean,
    default: false,
  },
  estimatedCredits: {
    type: Number,
    default: 0,
  },
  placement: {
    type: String,
    default: "workspace",
  },
});

const emit = defineEmits(["back", "confirm", "update-item", "reorder-items"]);

function handleItemUpdate(index, patch) {
  emit("update-item", index, patch);
}
</script>

<template>
  <StrategyReviewShell
    :loading="loading"
    :brief="brief"
    :items="items"
    title="视频脚本策略"
    :meta-text="metaText"
    loading-title="生成中..."
    loading-description="正在根据视频方向、素材和补充要求生成可编辑脚本策略。"
    success-title="视频脚本已生成"
    :confirm-text="`生成视频 · ${estimatedCredits || '-'} 积分`"
    :dirty="dirty"
    dirty-text="配置已变化，建议重新生成脚本"
    :placement="placement"
    :show-item-count="false"
    @back="emit('back')"
    @confirm="emit('confirm')"
    @update-item="handleItemUpdate"
    @reorder-items="emit('reorder-items', $event)"
  >
    <template #item="{ item, index, compact, updateItem }">
      <VideoStrategyCard
        :item="item"
        :index="index"
        :compact="compact"
        @update="(_, patch) => updateItem(patch)"
      />
    </template>
  </StrategyReviewShell>
</template>
