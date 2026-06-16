<script setup>
defineProps({
  state: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["save", "add-package", "remove-package"]);

const paymentConfigLabels = {
  zpay_pid_configured: "商户 ID",
  zpay_key_configured: "商户密钥",
  zpay_notify_url_configured: "异步回调地址",
  zpay_return_url_configured: "支付返回地址",
};
</script>

<template>
  <section class="space-y-4">
    <div v-if="state.loading" class="rounded-xl border border-slate-200 bg-white px-4 py-10 text-center text-sm text-slate-400">
      正在加载配置...
    </div>

    <template v-else>
      <div class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div class="mb-4 flex items-center justify-between">
          <div>
            <h2 class="text-sm font-black text-slate-800">生图扣费</h2>
            <p class="mt-1 text-xs text-slate-400">按分辨率配置每张图消耗积分。</p>
          </div>
        </div>
        <div class="grid gap-3 md:grid-cols-3">
          <label v-for="resolution in ['1K', '2K', '4K']" :key="resolution" class="block">
            <span class="text-xs font-bold text-slate-600">{{ resolution }} 扣费</span>
            <input v-model.number="state.imageCreditCosts[resolution]" type="number" min="1" class="mt-1 w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-primary" />
          </label>
        </div>
      </div>

      <div class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div class="mb-4 flex items-center justify-between gap-3">
          <div>
            <h2 class="text-sm font-black text-slate-800">充值套餐</h2>
            <p class="mt-1 text-xs text-slate-400">金额单位为分，保存后用户充值弹窗立即读取新配置。</p>
          </div>
          <button type="button" class="rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50" @click="emit('add-package')">
            新增套餐
          </button>
        </div>
        <div class="space-y-3">
          <div v-for="(pkg, index) in state.rechargePackages" :key="pkg.id || index" class="grid gap-2 rounded-xl border border-slate-100 bg-slate-50 p-3 md:grid-cols-[1fr_1.2fr_0.8fr_0.8fr_0.8fr_auto_auto]">
            <input v-model="pkg.id" type="text" class="rounded-lg border border-slate-200 px-2.5 py-2 text-xs outline-none focus:border-primary" placeholder="套餐ID" />
            <input v-model="pkg.name" type="text" class="rounded-lg border border-slate-200 px-2.5 py-2 text-xs outline-none focus:border-primary" placeholder="套餐名称" />
            <input v-model.number="pkg.credits" type="number" min="1" class="rounded-lg border border-slate-200 px-2.5 py-2 text-xs outline-none focus:border-primary" placeholder="积分" />
            <input v-model.number="pkg.amount_cents" type="number" min="1" class="rounded-lg border border-slate-200 px-2.5 py-2 text-xs outline-none focus:border-primary" placeholder="金额(分)" />
            <input v-model="pkg.badge" type="text" class="rounded-lg border border-slate-200 px-2.5 py-2 text-xs outline-none focus:border-primary" placeholder="标签" />
            <label class="flex items-center justify-center gap-1.5 text-xs font-bold text-slate-600">
              <input v-model="pkg.enabled" type="checkbox" class="h-4 w-4 rounded border-slate-300 text-primary" />
              启用
            </label>
            <button type="button" class="rounded-lg border border-rose-200 px-2.5 py-2 text-xs font-bold text-rose-600 hover:bg-rose-50" @click="emit('remove-package', index)">
              删除
            </button>
          </div>
        </div>
      </div>

      <div class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <h2 class="text-sm font-black text-slate-800">支付配置状态</h2>
        <div class="mt-3 grid gap-3 md:grid-cols-4">
          <div v-for="(value, key) in state.paymentConfig" :key="key" class="rounded-lg bg-slate-50 px-3 py-2">
            <p class="text-[11px] font-semibold text-slate-400">{{ paymentConfigLabels[key] || key }}</p>
            <p class="mt-1 text-xs font-bold" :class="value ? 'text-emerald-600' : 'text-rose-600'">{{ value ? '已配置' : '未配置' }}</p>
          </div>
        </div>
      </div>

      <div class="flex justify-end">
        <button type="button" class="rounded-xl bg-primary px-5 py-2 text-xs font-black text-white disabled:opacity-50" :disabled="state.saving" @click="emit('save')">
          {{ state.saving ? '保存中...' : '保存配置' }}
        </button>
      </div>
    </template>
  </section>
</template>
