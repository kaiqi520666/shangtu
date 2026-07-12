<script setup>
import { reactive, watch } from "vue";
import { formatMoney, formatTime } from "@/constants/admin.js";
import AppPagination from "@/components/ui/AppPagination.vue";

const props = defineProps({ state: { type: Object, required: true }, ownRate: { type: Number, required: true }, level: { type: Number, required: true } });
const emit = defineEmits(["update-rate", "change-page"]);
const rates = reactive({});
watch(() => props.state.items, (items) => items.forEach((item) => { rates[item.id] = Number(item.commission_rate).toFixed(2); }), { immediate: true });
</script>

<template>
  <div class="overflow-x-auto rounded-lg border border-slate-200 bg-white">
    <table class="w-full min-w-[900px] text-left text-xs">
      <thead class="bg-slate-50 text-slate-400"><tr><th class="px-4 py-3">用户</th><th class="px-4 py-3">等级</th><th class="px-4 py-3">比例</th><th class="px-4 py-3">累计充值</th><th class="px-4 py-3">累计消费</th><th class="px-4 py-3">贡献佣金</th><th class="px-4 py-3">注册时间</th></tr></thead>
      <tbody>
        <tr v-if="state.loading"><td colspan="7" class="px-4 py-12 text-center text-slate-400">正在加载下级...</td></tr>
        <tr v-else-if="!state.items.length"><td colspan="7" class="px-4 py-12 text-center text-slate-400">暂无下级用户</td></tr>
        <tr v-for="item in state.items" v-else :key="item.id" class="border-t border-slate-100">
          <td class="px-4 py-3"><p class="font-bold text-slate-800">{{ item.username }}</p><p class="text-slate-400">{{ item.email }}</p></td><td class="px-4 py-3 font-bold">{{ item.level }} 级</td>
          <td class="px-4 py-3"><div v-if="item.level === level + 1" class="flex items-center gap-2"><input v-model="rates[item.id]" type="number" min="0" :max="ownRate" step="0.01" class="w-20 rounded-lg border border-slate-200 px-2 py-1.5 outline-none focus:border-primary" /><button type="button" class="font-bold text-primary" @click="emit('update-rate', item.id, rates[item.id])">保存</button></div><span v-else>{{ Number(item.commission_rate).toFixed(2) }}%</span></td>
          <td class="px-4 py-3 font-bold text-slate-700">{{ formatMoney(item.recharge_cents) }}</td><td class="px-4 py-3">{{ item.consumed_credits }} 点</td><td class="px-4 py-3 font-bold text-emerald-600">{{ formatMoney(item.contributed_commission_cents) }}</td><td class="px-4 py-3 text-slate-500">{{ formatTime(item.created_at) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
  <div class="mt-4"><AppPagination :state="state" @change-page="emit('change-page', $event)" /></div>
</template>
