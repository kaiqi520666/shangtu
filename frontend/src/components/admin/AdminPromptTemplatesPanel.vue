<script setup>
import {
  activeStatusLabel,
  activeStatusOptions,
  formatTime,
  promptModelOptions,
  promptPurposeLabel,
  promptPurposeOptions,
  promptScenarioOptions,
  promptTemplateScopeLabel,
  scenarioLabel,
} from "@/constants/admin.js";
import AppCheckbox from "@/components/ui/AppCheckbox.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import AdminPagination from "./AdminPagination.vue";

defineProps({
  state: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["apply-filter", "change-page", "create", "edit", "toggle"]);
</script>

<template>
  <section class="space-y-4">
    <div class="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
      <input v-model="state.keyword" type="text" class="min-w-72 rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none" placeholder="搜索名称、内容、平台" @keyup.enter="emit('apply-filter')" />
      <div class="w-36">
        <AppSelect v-model="state.scenario" :options="promptScenarioOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <div class="w-36">
        <AppSelect v-model="state.purpose" :options="promptPurposeOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <div class="w-40">
        <AppSelect v-model="state.model" :options="promptModelOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <input v-model="state.type_id" type="text" class="w-44 rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none" placeholder="方向 / 图种 type_id" @keyup.enter="emit('apply-filter')" />
      <div class="w-32">
        <AppSelect v-model="state.active" :options="activeStatusOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <button type="button" class="rounded-lg bg-primary px-3 py-2 text-xs font-bold text-white" @click="emit('apply-filter')">查询</button>
      <button type="button" class="rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50" @click="emit('create')">新增模板</button>
      <span class="ml-auto text-xs text-slate-400">共 {{ state.total }} 个模板</span>
    </div>

    <div class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
      <table class="w-full text-left text-xs">
        <thead class="bg-slate-50 text-slate-400">
          <tr>
            <th class="px-4 py-3 font-semibold">模板</th>
            <th class="px-4 py-3 font-semibold">适用范围</th>
            <th class="px-4 py-3 font-semibold">模型</th>
            <th class="px-4 py-3 font-semibold">内容预览</th>
            <th class="px-4 py-3 font-semibold">状态</th>
            <th class="px-4 py-3 font-semibold">更新时间</th>
            <th class="px-4 py-3 font-semibold">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="state.loading">
            <td colspan="7" class="px-4 py-10 text-center text-slate-400">加载中...</td>
          </tr>
          <tr v-else-if="!state.items.length">
            <td colspan="7" class="px-4 py-10 text-center text-slate-400">暂无提示词模板</td>
          </tr>
          <tr v-for="template in state.items" v-else :key="template.id" class="border-t border-slate-100 align-top">
            <td class="px-4 py-3">
              <p class="font-bold text-slate-800">{{ template.name }}</p>
              <p class="mt-0.5 text-slate-400">v{{ template.version }} · {{ promptPurposeLabel(template.purpose, template.scenario) }}</p>
            </td>
            <td class="px-4 py-3 text-slate-600">
              <p>{{ scenarioLabel(template.scenario) }}</p>
              <p class="mt-0.5 text-slate-400">{{ template.platform || '全部平台' }} / {{ promptTemplateScopeLabel(template) }}</p>
            </td>
            <td class="px-4 py-3 text-slate-600">{{ template.model }}</td>
            <td class="px-4 py-3">
              <p class="line-clamp-2 max-w-md text-slate-500">{{ template.content }}</p>
            </td>
            <td class="px-4 py-3">
              <AppCheckbox :model-value="template.active" :label="activeStatusLabel(template.active)" @change="emit('toggle', template)" />
            </td>
            <td class="px-4 py-3 text-slate-500">{{ formatTime(template.updated_at || template.created_at) }}</td>
            <td class="px-4 py-3">
              <button type="button" class="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-bold text-slate-600 hover:bg-slate-50" @click="emit('edit', template)">编辑</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <AdminPagination :state="state" @change-page="emit('change-page', $event)" />
  </section>
</template>
