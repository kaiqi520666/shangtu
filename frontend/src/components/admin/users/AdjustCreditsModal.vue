<script setup>
import { reactive, watch } from "vue";
import AppModal from "@/components/ui/AppModal.vue";

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  target: {
    type: Object,
    default: null,
  },
  saving: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["close", "submit"]);

const localForm = reactive({
  amount: "",
  note: "",
});

watch(
  () => [props.open, props.target?.id],
  () => {
    if (!props.open) return;
    localForm.amount = "";
    localForm.note = "";
  },
  { immediate: true },
);

function submit() {
  emit("submit", {
    amount: localForm.amount,
    note: localForm.note,
  });
}
</script>

<template>
  <AppModal :open="open" title="调整积分" subtitle="必须填写备注，操作会写入积分流水和审计日志" @close="emit('close')">
    <div class="space-y-4 p-5">
      <div v-if="target" class="rounded-xl bg-slate-50 px-4 py-3 text-xs text-slate-600">
        <p class="font-bold text-slate-800">{{ target.email }}</p>
        <p class="mt-1">当前余额：{{ target.credits }} 点</p>
      </div>
      <label class="block">
        <span class="text-xs font-bold text-slate-600">调整积分</span>
        <input
          v-model="localForm.amount"
          type="number"
          class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary"
          placeholder="正数加积分，负数扣积分"
        />
      </label>
      <label class="block">
        <span class="text-xs font-bold text-slate-600">备注</span>
        <textarea
          v-model="localForm.note"
          rows="3"
          class="mt-1 w-full resize-none rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary"
          placeholder="例如：客服补偿、异常扣回"
        ></textarea>
      </label>
    </div>
    <template #footer>
      <button type="button" class="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600" @click="emit('close')">取消</button>
      <button type="button" class="rounded-xl bg-primary px-4 py-2 text-xs font-bold text-white disabled:opacity-50" :disabled="saving" @click="submit">
        {{ saving ? '保存中...' : '确认调整' }}
      </button>
    </template>
  </AppModal>
</template>
