<script setup>
import StrategyReviewShell from "@/components/generation/workspace/StrategyReviewShell.vue";
import ProductSuiteStrategyCard from "@/components/product-suite/ProductSuiteStrategyCard.vue";

defineProps({
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
  totalCount: {
    type: Number,
    default: 0,
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
    title="套图策略与设计规范"
    :meta-text="`${settings.platform} / ${settings.language} / ${selectedImageLabel}`"
    loading-title="生成中..."
    loading-description="正在根据商品图片、套图结构、平台规则和卖点要求，生成可编辑的套图策略。"
    success-title="套图策略已生成"
    item-unit="个套图类型"
    :confirm-text="`生成套图（${totalCount}张）`"
    :dirty="dirty"
    dirty-text="配置已变化，建议重新生成策略"
    :placement="placement"
    @back="emit('back')"
    @confirm="emit('confirm')"
    @update-item="handleItemUpdate"
    @reorder-items="emit('reorder-items', $event)"
    @remove-item="emit('remove-item', $event)"
  >
    <template #item="{ item, index, compact, updateItem, removeItem }">
      <ProductSuiteStrategyCard
        :item="item"
        :index="index"
        :compact="compact"
        @update="(_, patch) => updateItem(patch)"
        @remove="removeItem"
      />
    </template>
  </StrategyReviewShell>
</template>
