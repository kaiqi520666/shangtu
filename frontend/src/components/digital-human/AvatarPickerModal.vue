<script setup>
import { computed, ref, watch } from "vue";
import { Bot, ExternalLink, PlayCircle } from "lucide-vue-next";
import { getDigitalHumanAvatars } from "@/api/digitalHuman.js";
import DigitalHumanPickerPlaceholder from "@/components/digital-human/DigitalHumanPickerPlaceholder.vue";
import HeygenPickerModalShell from "@/components/digital-human/HeygenPickerModalShell.vue";
import AppModal from "@/components/ui/AppModal.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import { useHeygenResourcePicker } from "@/composables/digital-human/useHeygenResourcePicker.js";
import {
  heygenAvatarEngineLabel,
  heygenAvatarEngineOptions,
  heygenAvatarOrientationOptions,
  heygenGenderOptions,
} from "@/constants/admin.js";

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  selectedAvatar: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(["close", "confirm", "notify"]);

const tabs = [
  { value: "system", label: "系统数字人" },
  { value: "custom", label: "我的数字人" },
];
const avatarGenderOptions = heygenGenderOptions.filter((item) => item.value !== "unknown");

const activeTab = ref("system");
const pendingAvatar = ref(null);
const previewItem = ref(null);
const picker = useHeygenResourcePicker({
  listApi: getDigitalHumanAvatars,
  defaultFilters: {
    gender: "",
    orientation: "",
    engine: "",
  },
  buildParams: ({ page, pageSize, keyword, filters }) => ({
    page,
    page_size: pageSize,
    keyword: keyword || undefined,
    gender: filters.gender || undefined,
    orientation: filters.orientation || undefined,
    engine: filters.engine || undefined,
  }),
});

const summary = computed(() => `共 ${picker.state.total} 个系统数字人`);

watch(
  () => props.open,
  async (open) => {
    if (!open) {
      previewItem.value = null;
      return;
    }
    activeTab.value = "system";
    pendingAvatar.value = props.selectedAvatar || null;
    await initSystemTab();
  },
);

async function initSystemTab() {
  picker.reset();
  const result = await picker.reload();
  if (!result.ok) {
    emit("notify", result.message || "系统数字人加载失败");
  }
}

async function handleTabChange(value) {
  activeTab.value = value;
  if (value === "system") {
    await initSystemTab();
  }
}

async function applyFilters() {
  const result = await picker.reload();
  if (!result.ok) {
    emit("notify", result.message || "系统数字人加载失败");
  }
}

async function handleReachEnd(event) {
  if (activeTab.value !== "system") return;
  const result = await picker.handleScroll(event);
  if (!result.ok) {
    emit("notify", result.message || "系统数字人加载失败");
  }
}

function selectAvatar(item) {
  pendingAvatar.value = item;
}

function isSelected(item) {
  return pendingAvatar.value?.id === item.id;
}

function confirmSelection() {
  if (!pendingAvatar.value) {
    emit("notify", "请选择系统数字人");
    return;
  }
  emit("confirm", pendingAvatar.value);
  emit("close");
}
</script>

<template>
  <HeygenPickerModalShell
    :open="open"
    title="选择数字人"
    subtitle="当前先支持系统数字人，下一批接入训练数字人和照片数字人"
    :tabs="tabs"
    :active-tab="activeTab"
    :keyword="picker.state.keyword"
    search-placeholder="搜索名称、avatar_id、group_id"
    :summary="activeTab === 'system' ? summary : ''"
    :show-toolbar="activeTab === 'system'"
    :loading-more="picker.state.loadingMore"
    @close="emit('close')"
    @change-tab="handleTabChange"
    @update:keyword="picker.state.keyword = $event"
    @search="applyFilters"
    @reach-end="handleReachEnd"
  >
    <template #filters>
      <div class="w-28">
        <AppSelect v-model="picker.filters.gender" :options="avatarGenderOptions" @update:model-value="applyFilters" />
      </div>
      <div class="w-28">
        <AppSelect v-model="picker.filters.orientation" :options="heygenAvatarOrientationOptions" @update:model-value="applyFilters" />
      </div>
      <div class="w-32">
        <AppSelect v-model="picker.filters.engine" :options="heygenAvatarEngineOptions" @update:model-value="applyFilters" />
      </div>
    </template>

    <DigitalHumanPickerPlaceholder
      v-if="activeTab === 'custom'"
      :icon="Bot"
      title="定制数字人下一批开放"
      description="这里会接入训练数字人、照片数字人和你的专属角色管理。"
      action-text="创建我的数字人"
    />

    <div v-else-if="picker.state.loading" class="flex min-h-[420px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-400">
      正在加载系统数字人...
    </div>

    <div v-else-if="!picker.state.items.length" class="flex min-h-[420px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-400">
      暂无可用系统数字人
    </div>

    <div v-else class="grid gap-4 md:grid-cols-3 xl:grid-cols-4">
      <article
        v-for="item in picker.state.items"
        :key="item.id"
        class="cursor-pointer overflow-hidden rounded-2xl border bg-white shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md"
        :class="isSelected(item) ? 'border-primary ring-2 ring-primary/10' : 'border-slate-200'"
        @click="selectAvatar(item)"
      >
        <div class="relative aspect-[4/5] bg-slate-100">
          <img v-if="item.preview_image_url" :src="item.preview_image_url" class="h-full w-full object-cover" alt="数字人预览" />
          <div v-else class="flex h-full items-center justify-center text-xs text-slate-400">无预览图</div>
          <span v-if="isSelected(item)" class="absolute right-3 top-3 rounded-full bg-primary px-2.5 py-1 text-[11px] font-bold text-white">
            已选择
          </span>
        </div>

        <div class="space-y-2 p-4">
          <div>
            <h3 class="truncate text-sm font-black text-slate-800">{{ item.name }}</h3>
            <p class="mt-1 text-xs text-slate-400">{{ item.gender || "未知性别" }} / {{ item.preferred_orientation || "未标注方向" }}</p>
          </div>

          <p class="truncate text-[11px] text-slate-400" :title="item.avatar_id">avatar_id：{{ item.avatar_id }}</p>

          <div class="flex flex-wrap gap-1">
            <span v-for="engine in item.supported_api_engines" :key="engine" class="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-medium text-slate-500">
              {{ heygenAvatarEngineLabel(engine) }}
            </span>
          </div>

          <div class="flex items-center justify-between gap-2 pt-1">
            <button
              v-if="item.preview_video_url || item.preview_image_url"
              type="button"
              class="inline-flex items-center gap-1 text-[11px] font-bold text-primary hover:text-secondary"
              @click.stop="previewItem = item"
            >
              <PlayCircle class="h-3.5 w-3.5" />
              预览
            </button>
            <a
              v-if="item.preview_video_url"
              :href="item.preview_video_url"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-1 text-[11px] font-medium text-slate-400 hover:text-slate-600"
              @click.stop
            >
              <ExternalLink class="h-3.5 w-3.5" />
              打开
            </a>
          </div>
        </div>
      </article>
    </div>

    <template #footer>
      <div class="flex items-center justify-between gap-3">
        <p class="text-xs text-slate-400">{{ pendingAvatar?.name ? `已选：${pendingAvatar.name}` : "请选择 1 个数字人" }}</p>
        <div class="flex items-center gap-2">
          <button type="button" class="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50" @click="emit('close')">取消</button>
          <button type="button" class="rounded-xl bg-primary px-4 py-2 text-xs font-bold text-white transition-colors hover:bg-secondary" @click="confirmSelection">确认数字人</button>
        </div>
      </div>
    </template>
  </HeygenPickerModalShell>

  <AppModal :open="Boolean(previewItem)" title="数字人预览" panel-class="w-full max-w-3xl" @close="previewItem = null">
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
</template>
