<script setup>
import StrategyReviewShell from "@/components/generation/workspace/StrategyReviewShell.vue";
import OutfitStrategyCard from "@/components/outfit/OutfitStrategyCard.vue";

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
  settings: {
    type: Object,
    required: true,
  },
  selectedImageLabel: {
    type: String,
    required: true,
  },
  dirty: {
    type: Boolean,
    default: false,
  },
  placement: {
    type: String,
    default: "workspace",
  },
});

const emit = defineEmits(["back", "confirm", "update-item", "reorder-items", "remove-item"]);

function handleItemUpdate(index, patch) {
  emit("update-item", index, patch);
}
</script>

<template>
  <StrategyReviewShell
    :loading="loading"
    :brief="brief"
    :items="items"
    title="穿搭方案与保真约束"
    :meta-text="`${settings.platform} / ${settings.language} / ${selectedImageLabel}`"
    loading-title="生成中..."
    loading-description="正在根据服装图、模特参考和拍摄场景，生成可编辑的穿搭方案。"
    success-title="穿搭方案已生成"
    item-unit="个场景"
    :confirm-text="`生成穿搭图（${items.length}张）`"
    :dirty="dirty"
    dirty-text="配置已变化，建议重新生成方案"
    :placement="placement"
    @back="emit('back')"
    @confirm="emit('confirm')"
    @update-item="handleItemUpdate"
    @reorder-items="emit('reorder-items', $event)"
    @remove-item="emit('remove-item', $event)"
  >
    <template #item="{ item, index, compact, updateItem, removeItem }">
      <OutfitStrategyCard
        :item="item"
        :index="index"
        :compact="compact"
        @update="(_, patch) => updateItem(patch)"
        @remove="removeItem"
      />
    </template>
  </StrategyReviewShell>
</template>
