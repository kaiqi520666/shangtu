<script setup>
import { reactive, watch } from "vue";
import AppModal from "@/components/ui/AppModal.vue";

const props = defineProps({ action: { type: String, default: "" }, target: { type: Object, default: null }, saving: { type: Boolean, default: false } });
const emit = defineEmits(["close", "submit"]);
const form = reactive({ reason: "", paymentReference: "", voucher: null });

watch(() => props.action, () => {
  form.reason = "";
  form.paymentReference = "";
  form.voucher = null;
});

function submit() {
  if (props.action === "reject") emit("submit", { reason: form.reason.trim() });
  else emit("submit", { paymentReference: form.paymentReference.trim(), voucher: form.voucher });
}
</script>

<template>
  <AppModal :open="Boolean(action)" :title="action === 'reject' ? '驳回提现' : '确认打款'" :subtitle="target?.user_email || ''" @close="emit('close')">
    <div class="space-y-4 p-5">
      <label v-if="action === 'reject'" class="block">
        <span class="text-xs font-bold text-slate-600">驳回原因</span>
        <textarea v-model="form.reason" rows="3" class="mt-1 w-full resize-none rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary"></textarea>
      </label>
      <template v-else>
        <label class="block"><span class="text-xs font-bold text-slate-600">打款流水号</span><input v-model="form.paymentReference" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary" /></label>
        <label class="block"><span class="text-xs font-bold text-slate-600">打款凭证（可选）</span><input type="file" accept="image/jpeg,image/png,image/webp" class="mt-1 block w-full text-xs text-slate-500" @change="form.voucher = $event.target.files?.[0] || null" /></label>
      </template>
      <div class="flex justify-end gap-2">
        <button type="button" class="rounded-lg border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600" @click="emit('close')">取消</button>
        <button type="button" class="rounded-lg bg-primary px-4 py-2 text-xs font-bold text-white disabled:opacity-50" :disabled="saving || (action === 'reject' ? !form.reason.trim() : !form.paymentReference.trim())" @click="submit">{{ saving ? '处理中...' : '确认' }}</button>
      </div>
    </div>
  </AppModal>
</template>
