<script setup>
import {
  activeStatusLabel,
  activeStatusOptions,
  formatTime,
  productCatalogScenarioLabel,
  scenarioOptions,
} from "@/constants/admin.js";
import AppCheckbox from "@/components/ui/AppCheckbox.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import AdminPagination from "../AdminPagination.vue";

const catalogScenarioOptions = [
  { label: "全部目录", value: "" },
  ...scenarioOptions.filter((option) => ["product_image", "product_suite", "outfit"].includes(option.value)),
];

defineProps({
  state: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["apply-filter", "change-page", "edit", "toggle"]);
</script>

<template>
  <section class="space-y-4">
    <div class="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
      <input
        v-model="state.keyword"
        type="text"
        class="min-w-72 rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none"
        placeholder="搜索名称、ID、描述或策略"
        @keyup.enter="emit('apply-filter')"
      />
      <div class="w-36">
        <AppSelect v-model="state.scenario" :options="catalogScenarioOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <div class="w-32">
        <AppSelect v-model="state.enabled" :options="activeStatusOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <button type="button" class="rounded-lg bg-primary px-3 py-2 text-xs font-bold text-white" @click="emit('apply-filter')">查询</button>
      <span class="ml-auto text-xs text-slate-400">共 {{ state.total }} 个目录项</span>
    </div>

    <div class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <table class="w-full text-left text-xs">
        <thead class="bg-slate-50 text-slate-400">
          <tr>
            <th class="px-4 py-3 font-semibold">目录项</th>
            <th class="px-4 py-3 font-semibold">场景</th>
            <th class="px-4 py-3 font-semibold">展示描述</th>
            <th class="px-4 py-3 font-semibold">生成策略</th>
            <th class="px-4 py-3 font-semibold">数量</th>
            <th class="px-4 py-3 font-semibold">排序</th>
            <th class="px-4 py-3 font-semibold">状态</th>
            <th class="px-4 py-3 font-semibold">更新时间</th>
            <th class="px-4 py-3 font-semibold">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="state.loading">
            <td colspan="9" class="px-4 py-10 text-center text-slate-400">加载中...</td>
          </tr>
          <tr v-else-if="!state.items.length">
            <td colspan="9" class="px-4 py-10 text-center text-slate-400">暂无商品目录</td>
          </tr>
          <tr v-for="item in state.items" v-else :key="item.id" class="border-t border-slate-100 align-top">
            <td class="px-4 py-3">
              <p class="font-bold text-slate-800">{{ item.name }}</p>
              <p class="mt-0.5 font-mono text-[11px] text-slate-400">{{ item.item_id }}</p>
            </td>
            <td class="px-4 py-3 text-slate-600">{{ productCatalogScenarioLabel(item.scenario) }}</td>
            <td class="px-4 py-3">
              <p class="line-clamp-2 max-w-xs text-slate-500">{{ item.description }}</p>
            </td>
            <td class="px-4 py-3">
              <p class="line-clamp-2 max-w-sm text-slate-500">{{ item.strategy }}</p>
            </td>
            <td class="px-4 py-3 text-slate-600">
              <span v-if="item.scenario === 'product_suite'">{{ item.default_count }} / {{ item.max_count }}</span>
              <span v-else class="text-slate-300">-</span>
            </td>
            <td class="px-4 py-3 text-slate-600">{{ item.sort }}</td>
            <td class="px-4 py-3">
              <AppCheckbox :model-value="item.enabled" :label="activeStatusLabel(item.enabled)" @change="emit('toggle', item)" />
            </td>
            <td class="px-4 py-3 text-slate-500">{{ formatTime(item.updated_at || item.created_at) }}</td>
            <td class="px-4 py-3">
              <button
                type="button"
                class="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-bold text-slate-600 hover:bg-slate-50"
                @click="emit('edit', item)"
              >
                编辑
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <AdminPagination :state="state" @change-page="emit('change-page', $event)" />
  </section>
</template>
