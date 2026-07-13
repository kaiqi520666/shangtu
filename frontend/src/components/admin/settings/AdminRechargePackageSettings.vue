<script setup>
import AppCheckbox from "@/components/ui/AppCheckbox.vue";

defineProps({
  packages: { type: Array, required: true },
});

const emit = defineEmits(["add", "remove"]);
</script>

<template>
  <section class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
    <div class="mb-4 flex items-center justify-between gap-3">
      <div>
        <h2 class="text-sm font-black text-slate-800">充值套餐</h2>
        <p class="mt-1 text-xs text-slate-400">金额单位为分，保存后用户充值弹窗立即读取新配置。</p>
      </div>
      <button type="button" class="rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50" @click="emit('add')">新增套餐</button>
    </div>
    <div class="space-y-3">
      <div v-for="(pkg, index) in packages" :key="pkg.id || index" class="grid gap-2 rounded-xl border border-slate-100 bg-slate-50 p-3 md:grid-cols-[1fr_1.2fr_0.8fr_0.8fr_0.8fr_auto_auto]">
        <input v-model="pkg.id" type="text" class="rounded-lg border border-slate-200 px-2.5 py-2 text-xs outline-none focus:border-primary" placeholder="套餐ID" />
        <input v-model="pkg.name" type="text" class="rounded-lg border border-slate-200 px-2.5 py-2 text-xs outline-none focus:border-primary" placeholder="套餐名称" />
        <input v-model.number="pkg.credits" type="number" min="1" class="rounded-lg border border-slate-200 px-2.5 py-2 text-xs outline-none focus:border-primary" placeholder="积分" />
        <input v-model.number="pkg.amount_cents" type="number" min="1" class="rounded-lg border border-slate-200 px-2.5 py-2 text-xs outline-none focus:border-primary" placeholder="金额(分)" />
        <input v-model="pkg.badge" type="text" class="rounded-lg border border-slate-200 px-2.5 py-2 text-xs outline-none focus:border-primary" placeholder="标签" />
        <div class="flex items-center justify-center">
          <AppCheckbox v-model="pkg.enabled" label="启用" />
        </div>
        <button type="button" class="rounded-lg border border-rose-200 px-2.5 py-2 text-xs font-bold text-rose-600 hover:bg-rose-50" @click="emit('remove', index)">删除</button>
      </div>
    </div>
  </section>
</template>
