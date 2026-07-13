<script setup>
defineProps({
  config: { type: Object, required: true },
});

const labels = {
  zpay_pid_configured: "商户 ID",
  zpay_key_configured: "商户密钥",
  zpay_notify_url_configured: "异步回调地址",
  zpay_return_url_configured: "支付返回地址",
};
</script>

<template>
  <section class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
    <h2 class="text-sm font-black text-slate-800">支付配置状态</h2>
    <div class="mt-3 grid gap-3 md:grid-cols-4">
      <div v-for="(value, key) in config" :key="key" class="rounded-lg bg-slate-50 px-3 py-2">
        <p class="text-[11px] font-semibold text-slate-400">{{ labels[key] || key }}</p>
        <p class="mt-1 text-xs font-bold" :class="value ? 'text-emerald-600' : 'text-rose-600'">{{ value ? '已配置' : '未配置' }}</p>
      </div>
    </div>
  </section>
</template>
