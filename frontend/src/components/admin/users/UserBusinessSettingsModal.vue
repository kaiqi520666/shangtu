<script setup>
import { reactive, watch } from "vue";
import AppCheckbox from "@/components/ui/AppCheckbox.vue";
import AppModal from "@/components/ui/AppModal.vue";

const props = defineProps({
  open: { type: Boolean, default: false },
  target: { type: Object, default: null },
  saving: { type: Boolean, default: false },
});
const emit = defineEmits(["close", "submit"]);
const form = reactive({ consumptionMultiplier: "1.00", distributionEnabled: false, commissionRate: "10.00" });

watch(
  () => [props.open, props.target?.id],
  () => {
    if (!props.open || !props.target) return;
    form.consumptionMultiplier = Number(props.target.consumption_multiplier || 1).toFixed(2);
    form.distributionEnabled = Boolean(props.target.distribution_enabled);
    form.commissionRate = Number(props.target.commission_rate ?? 10).toFixed(2);
  },
  { immediate: true },
);

function submit() {
  const canManageDistribution = !props.target?.distribution_level || props.target.distribution_level === 1;
  emit("submit", {
    consumption_multiplier: Number(form.consumptionMultiplier),
    ...(canManageDistribution ? { distribution_enabled: form.distributionEnabled } : {}),
    ...(canManageDistribution && (form.distributionEnabled || props.target?.distribution_level === 1)
      ? { commission_rate: Number(form.commissionRate) } : {}),
  });
}
</script>

<template>
  <AppModal :open="open" title="业务设置" :subtitle="target?.email || ''" @close="emit('close')">
    <div class="space-y-5 p-5">
      <label class="block">
        <span class="text-xs font-bold text-slate-600">消费倍率</span>
        <input v-model="form.consumptionMultiplier" type="number" min="0.01" max="9.99" step="0.01" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary" />
      </label>
      <div v-if="!target?.distribution_level || target?.distribution_level === 1" class="space-y-4 border-t border-slate-100 pt-4">
        <AppCheckbox v-model="form.distributionEnabled" label="启用一级分销" />
        <label v-if="form.distributionEnabled || target?.distribution_level === 1" class="block">
          <span class="text-xs font-bold text-slate-600">一级佣金比例（%）</span>
          <input v-model="form.commissionRate" type="number" min="0" max="100" step="0.01" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary" />
        </label>
      </div>
      <p v-else class="border-t border-slate-100 pt-4 text-xs font-semibold text-slate-500">该用户是 {{ target.distribution_level }} 级分销用户，比例由其直接上级管理。</p>
    </div>
    <template #footer>
      <button type="button" class="rounded-lg border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600" @click="emit('close')">取消</button>
      <button type="button" class="rounded-lg bg-primary px-4 py-2 text-xs font-bold text-white disabled:opacity-50" :disabled="saving" @click="submit">{{ saving ? '保存中...' : '保存' }}</button>
    </template>
  </AppModal>
</template>
