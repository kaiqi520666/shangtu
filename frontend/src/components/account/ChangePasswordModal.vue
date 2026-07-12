<script setup>
import { reactive, watch } from "vue";
import AppModal from "@/components/ui/AppModal.vue";
import PasswordInput from "@/components/ui/PasswordInput.vue";

const props = defineProps({ open: { type: Boolean, default: false }, saving: { type: Boolean, default: false } });
const emit = defineEmits(["close", "submit"]);
const form = reactive({ currentPassword: "", newPassword: "", confirmPassword: "" });

watch(
  () => props.open,
  (open) => {
    if (open) Object.assign(form, { currentPassword: "", newPassword: "", confirmPassword: "" });
  },
);
</script>

<template>
  <AppModal :open="open" title="修改密码" subtitle="修改成功后，所有设备需要重新登录" @close="emit('close')">
    <form class="space-y-4 p-5" @submit.prevent="emit('submit', { ...form })">
      <PasswordInput v-model="form.currentPassword" label="当前密码" autocomplete="current-password" />
      <PasswordInput v-model="form.newPassword" label="新密码" autocomplete="new-password" placeholder="至少 6 个字符" />
      <PasswordInput v-model="form.confirmPassword" label="确认新密码" autocomplete="new-password" />
      <div class="flex justify-end gap-2 pt-1">
        <button type="button" class="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600" @click="emit('close')">取消</button>
        <button type="submit" class="rounded-xl bg-primary px-4 py-2 text-xs font-bold text-white disabled:opacity-50" :disabled="saving">
          {{ saving ? "修改中..." : "确认修改" }}
        </button>
      </div>
    </form>
  </AppModal>
</template>
