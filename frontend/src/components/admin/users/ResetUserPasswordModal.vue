<script setup>
import { reactive, watch } from "vue";
import AppModal from "@/components/ui/AppModal.vue";
import PasswordInput from "@/components/ui/PasswordInput.vue";

const props = defineProps({
  open: { type: Boolean, default: false },
  target: { type: Object, default: null },
  saving: { type: Boolean, default: false },
});
const emit = defineEmits(["close", "submit"]);
const form = reactive({ newPassword: "", confirmPassword: "" });

watch(
  () => [props.open, props.target?.id],
  () => {
    if (props.open) Object.assign(form, { newPassword: "", confirmPassword: "" });
  },
);
</script>

<template>
  <AppModal :open="open" title="重置密码" :subtitle="target?.email || ''" @close="emit('close')">
    <form id="reset-user-password-form" class="space-y-4 p-5" @submit.prevent="emit('submit', { ...form })">
      <p class="rounded-xl bg-amber-50 px-4 py-3 text-xs font-semibold leading-5 text-amber-700">重置后，该用户所有设备上的登录状态会立即失效。</p>
      <PasswordInput v-model="form.newPassword" label="新密码" autocomplete="new-password" placeholder="至少 6 个字符" />
      <PasswordInput v-model="form.confirmPassword" label="确认新密码" autocomplete="new-password" />
    </form>
    <template #footer>
      <button type="button" class="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600" @click="emit('close')">取消</button>
      <button type="submit" form="reset-user-password-form" class="rounded-xl bg-primary px-4 py-2 text-xs font-bold text-white disabled:opacity-50" :disabled="saving">
        {{ saving ? "重置中..." : "确认重置" }}
      </button>
    </template>
  </AppModal>
</template>
