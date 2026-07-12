<script setup>
import StrategyReviewShell from "@/components/generation/workspace/StrategyReviewShell.vue";
import StrategyModuleCard from "@/components/product-image/StrategyModuleCard.vue";

defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  brief: {
    type: String,
    default: "",
  },
  modules: {
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

const emit = defineEmits(["back", "confirm", "update-module", "reorder-modules", "remove-module"]);

function handleModuleUpdate(index, patch) {
  emit("update-module", index, patch);
}
</script>

<template>
  <StrategyReviewShell
    :loading="loading"
    :brief="brief"
    :items="modules"
    title="模块策略与设计规范"
    :meta-text="`${settings.platform} / ${settings.language} / ${selectedImageLabel}`"
    loading-title="生成中..."
    loading-description="正在根据已选图种、平台规则和商品卖点，生成可编辑的模块内容与设计规范。"
    success-title="策略已生成"
    item-unit="个模块"
    :confirm-text="`生成详情图（${modules.length}张）`"
    :dirty="dirty"
    dirty-text="配置已变化，建议重新生成策略"
    :placement="placement"
    @back="emit('back')"
    @confirm="emit('confirm')"
    @update-item="handleModuleUpdate"
    @reorder-items="emit('reorder-modules', $event)"
    @remove-item="emit('remove-module', $event)"
  >
    <template #item="{ item, index, compact, updateItem, removeItem }">
      <StrategyModuleCard
        :module="item"
        :index="index"
        :compact="compact"
        @update="(_, patch) => updateItem(patch)"
        @remove="removeItem"
      />
    </template>
  </StrategyReviewShell>
</template>
