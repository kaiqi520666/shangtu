<script setup>
import AdminCreditCostSettings from "@/components/admin/settings/AdminCreditCostSettings.vue";
import AdminPaymentStatus from "@/components/admin/settings/AdminPaymentStatus.vue";
import AdminRechargePackageSettings from "@/components/admin/settings/AdminRechargePackageSettings.vue";

defineProps({
  state: { type: Object, required: true },
});

const emit = defineEmits(["save", "add-package", "remove-package"]);
</script>

<template>
  <section class="space-y-4">
    <div v-if="state.loading" class="rounded-xl border border-slate-200 bg-white px-4 py-10 text-center text-sm text-slate-400">正在加载配置...</div>
    <template v-else>
      <AdminCreditCostSettings :state="state" />
      <AdminRechargePackageSettings :packages="state.rechargePackages" @add="emit('add-package')" @remove="emit('remove-package', $event)" />
      <AdminPaymentStatus :config="state.paymentConfig" />
      <div class="flex justify-end">
        <button type="button" class="rounded-xl bg-primary px-5 py-2 text-xs font-black text-white disabled:opacity-50" :disabled="state.saving" @click="emit('save')">
          {{ state.saving ? '保存中...' : '保存配置' }}
        </button>
      </div>
    </template>
  </section>
</template>
