<script setup>
import { ExternalLink, LoaderCircle, PlayCircle, RefreshCw } from "lucide-vue-next";
import {
  activeStatusLabel,
  activeStatusOptions,
  formatTime,
  heygenAvatarEngineOptions,
  heygenAvatarEngineLabel,
  heygenAvatarOrientationOptions,
  heygenGenderOptions,
} from "@/constants/admin.js";
import AppCheckbox from "@/components/ui/AppCheckbox.vue";
import AppModal from "@/components/ui/AppModal.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import AdminPagination from "@/components/admin/AdminPagination.vue";

defineProps({
  state: {
    type: Object,
    required: true,
  },
  syncing: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["apply-filter", "change-page", "edit", "toggle", "sync"]);

const previewOpen = defineModel("previewOpen", { type: Boolean, default: false });
const previewItem = defineModel("previewItem", { type: Object, default: null });
</script>

<template>
  <section class="space-y-4">
    <div class="flex flex-wrap items-center gap-2 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
      <input v-model="state.keyword" type="text" class="min-w-72 rounded-lg border border-slate-200 px-3 py-2 text-xs outline-none" placeholder="搜索名称、avatar_id、group_id、默认声音" @keyup.enter="emit('apply-filter')" />
      <div class="w-28">
        <AppSelect v-model="state.gender" :options="heygenGenderOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <div class="w-28">
        <AppSelect v-model="state.orientation" :options="heygenAvatarOrientationOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <div class="w-32">
        <AppSelect v-model="state.engine" :options="heygenAvatarEngineOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <div class="w-32">
        <AppSelect v-model="state.active" :options="activeStatusOptions" @update:model-value="emit('apply-filter')" />
      </div>
      <button type="button" class="rounded-lg bg-primary px-3 py-2 text-xs font-bold text-white" @click="emit('apply-filter')">查询</button>
      <button type="button" class="flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50 disabled:opacity-50" :disabled="syncing || state.loading" @click="emit('sync')">
        <LoaderCircle v-if="syncing" class="h-3.5 w-3.5 animate-spin" />
        <RefreshCw v-else class="h-3.5 w-3.5" />
        {{ syncing ? "同步中..." : "同步 HeyGen" }}
      </button>
      <span class="ml-auto text-xs text-slate-400">共 {{ state.total }} 个系统数字人</span>
    </div>

    <div class="grid gap-4 md:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
      <div v-if="state.loading" class="col-span-full rounded-xl border border-slate-200 bg-white px-4 py-10 text-center text-sm text-slate-400">加载中...</div>
      <div v-else-if="!state.items.length" class="col-span-full rounded-xl border border-slate-200 bg-white px-4 py-10 text-center text-sm text-slate-400">暂无系统数字人</div>
      <article v-for="item in state.items" v-else :key="item.id" class="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div class="aspect-square bg-slate-100">
          <img v-if="item.preview_image_url" :src="item.preview_image_url" class="h-full w-full object-cover" />
          <div v-else class="flex h-full items-center justify-center text-xs text-slate-400">无预览</div>
        </div>
        <div class="space-y-2 p-3">
          <div class="flex items-start justify-between gap-2">
            <div class="min-w-0">
              <h3 class="truncate text-sm font-black text-slate-800">{{ item.name }}</h3>
              <p class="mt-0.5 text-xs text-slate-400">{{ item.gender || "-" }} / 排序 {{ item.sort_order }}</p>
            </div>
            <AppCheckbox :model-value="item.enabled" :label="activeStatusLabel(item.enabled)" @change="emit('toggle', item)" />
          </div>
          <p class="truncate text-[11px] text-slate-400" :title="item.avatar_id">avatar_id：{{ item.avatar_id }}</p>
          <p class="truncate text-[11px] text-slate-400" :title="item.default_voice_id || '-'">默认声音：{{ item.default_voice_id || "-" }}</p>
          <p class="text-[11px] text-slate-400">方向：{{ item.preferred_orientation || "-" }}</p>
          <div class="flex flex-wrap gap-1">
            <span v-for="engine in item.supported_api_engines" :key="engine" class="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-500">
              {{ heygenAvatarEngineLabel(engine) }}
            </span>
          </div>
          <div class="flex items-center justify-between gap-2 pt-1">
            <p class="text-[11px] text-slate-400">{{ formatTime(item.updated_at || item.created_at) }}</p>
            <div class="flex items-center gap-2">
              <button v-if="item.preview_video_url || item.preview_image_url" type="button" class="inline-flex items-center gap-1 text-[11px] font-medium text-primary hover:text-secondary" @click="previewItem = item; previewOpen = true">
                <PlayCircle class="h-3.5 w-3.5" />
                预览
              </button>
              <a v-if="item.preview_video_url" :href="item.preview_video_url" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 text-[11px] font-medium text-slate-400 hover:text-slate-600">
                <ExternalLink class="h-3 w-3" />
              </a>
            </div>
          </div>
          <button type="button" class="w-full rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-bold text-slate-600 hover:bg-slate-50" @click="emit('edit', item)">编辑</button>
        </div>
      </article>
    </div>

    <AdminPagination :state="state" @change-page="emit('change-page', $event)" />

    <AppModal :open="previewOpen" title="数字人预览" panel-class="w-full max-w-3xl" @close="previewOpen = false">
      <div v-if="previewItem" class="space-y-4 p-5">
        <video
          v-if="previewItem.preview_video_url"
          :src="previewItem.preview_video_url"
          class="max-h-[70vh] w-full rounded-xl bg-black object-contain"
          controls
          autoplay
          playsinline
        ></video>
        <img
          v-else-if="previewItem.preview_image_url"
          :src="previewItem.preview_image_url"
          class="max-h-[70vh] w-full rounded-xl bg-slate-100 object-contain"
          alt="数字人预览"
        />
      </div>
    </AppModal>
  </section>
</template>
