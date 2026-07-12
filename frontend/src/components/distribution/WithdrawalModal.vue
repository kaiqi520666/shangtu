<script setup>
import { reactive, watch } from "vue";
import AppModal from "@/components/ui/AppModal.vue";

const props = defineProps({ open: { type: Boolean, default: false }, saving: { type: Boolean, default: false } });
const emit = defineEmits(["close", "submit"]);
const form = reactive({ amount: "", alipayName: "", alipayAccount: "" });
watch(() => props.open, (open) => { if (open) Object.assign(form, { amount: "", alipayName: "", alipayAccount: "" }); });
function submit() { emit("submit", { amount_cents: Number(form.amount) * 100, alipay_name: form.alipayName.trim(), alipay_account: form.alipayAccount.trim() }); }
</script>

<template>
  <AppModal :open="open" title="申请提现" subtitle="最低 100 元，且为 100 元的整数倍" @close="emit('close')"><div class="space-y-4 p-5"><label class="block"><span class="text-xs font-bold text-slate-600">提现金额（元）</span><input v-model="form.amount" type="number" min="100" step="100" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary" /></label><label class="block"><span class="text-xs font-bold text-slate-600">支付宝姓名</span><input v-model="form.alipayName" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary" /></label><label class="block"><span class="text-xs font-bold text-slate-600">支付宝账号</span><input v-model="form.alipayAccount" class="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary" /></label><div class="flex justify-end gap-2"><button type="button" class="rounded-lg border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600" @click="emit('close')">取消</button><button type="button" class="rounded-lg bg-primary px-4 py-2 text-xs font-bold text-white disabled:opacity-50" :disabled="saving || !form.amount || !form.alipayName.trim() || !form.alipayAccount.trim()" @click="submit">{{ saving ? '提交中...' : '提交申请' }}</button></div></div></AppModal>
</template>
