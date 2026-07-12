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
const form = reactive({ code: "", credits: "", unlimited: true, usageLimit: "", enabled: true });

watch(
  () => [props.open, props.target?.id],
  () => {
    if (!props.open) return;
    Object.assign(form, {
      code: props.target?.code || "",
      credits: props.target?.credits || "",
      unlimited: props.target?.usage_limit == null,
      usageLimit: props.target?.usage_limit || "",
      enabled: props.target ? Boolean(props.target.enabled) : true,
    });
  },
  { immediate: true },
);
</script>

<template>
  <AppModal :open="open" :title="target ? '编辑优惠码' : '创建优惠码'" :subtitle="target ? '修改只影响未来兑换' : '优惠码创建后不可修改码值'" @close="emit('close')">
    <form class="space-y-4 p-5" @submit.prevent="emit('submit', { ...form })">
      <label class="block">
        <span class="text-xs font-bold text-slate-600">优惠码</span>
        <input v-model.trim="form.code" type="text" maxlength="32" :disabled="Boolean(target)" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-bold uppercase outline-none focus:border-primary disabled:bg-slate-100 disabled:text-slate-500" placeholder="例如 SUMMER2026" />
      </label>
      <label class="block">
        <span class="text-xs font-bold text-slate-600">赠送积分</span>
        <input v-model="form.credits" type="number" min="1" max="10000000" step="1" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary" />
      </label>
      <div class="space-y-3 border-t border-slate-100 pt-4">
        <AppCheckbox v-model="form.unlimited" label="无限使用次数" />
        <label v-if="!form.unlimited" class="block">
          <span class="text-xs font-bold text-slate-600">使用上限</span>
          <input v-model="form.usageLimit" type="number" :min="Math.max(1, target?.used_count || 0)" max="1000000" step="1" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary" />
          <span v-if="target?.used_count" class="mt-1 block text-[11px] font-semibold text-slate-400">当前已使用 {{ target.used_count }} 次</span>
        </label>
        <AppCheckbox v-model="form.enabled" label="启用优惠码" />
      </div>
      <div class="flex justify-end gap-2 pt-1">
        <button type="button" class="rounded-lg border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600" @click="emit('close')">取消</button>
        <button type="submit" class="rounded-lg bg-primary px-4 py-2 text-xs font-bold text-white disabled:opacity-50" :disabled="saving">{{ saving ? "保存中..." : "保存" }}</button>
      </div>
    </form>
  </AppModal>
</template>
