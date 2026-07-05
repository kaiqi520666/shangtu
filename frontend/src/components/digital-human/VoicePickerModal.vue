<script setup>
import { computed, ref, watch } from "vue";
import { LoaderCircle, Mic2, Trash2, UploadCloud } from "lucide-vue-next";
import {
  deleteDigitalHumanAudioAsset,
  getDigitalHumanAudioAssets,
  getDigitalHumanVoices,
  uploadDigitalHumanAudioAsset,
} from "@/api/digitalHuman.js";
import HeygenPickerModalShell from "@/components/digital-human/HeygenPickerModalShell.vue";
import ImageUploadSourcePanel from "@/components/generation/image/ImageUploadSourcePanel.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import { useHeygenResourcePicker } from "@/composables/digital-human/useHeygenResourcePicker.js";
import {
  heygenGenderOptions,
  heygenVoiceLanguageOptions,
  heygenVoiceLocaleOptions,
} from "@/constants/admin.js";

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  selectedVoice: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(["close", "confirm", "notify"]);

const tabs = [
  { value: "platform", label: "平台声音" },
  { value: "upload", label: "上传音频" },
];

const activeTab = ref("platform");
const pendingVoice = ref(null);
const fileInput = ref(null);
const uploadDragOver = ref(false);
const audioUploading = ref(false);
const deletingAudioId = ref("");

const platformPicker = useHeygenResourcePicker({
  listApi: getDigitalHumanVoices,
  defaultFilters: {
    language: "",
    gender: "",
    support_locale: "",
  },
  buildParams: ({ page, pageSize, keyword, filters }) => ({
    page,
    page_size: pageSize,
    keyword: keyword || undefined,
    language: filters.language || undefined,
    gender: filters.gender || undefined,
    support_locale: filters.support_locale || undefined,
  }),
});

const uploadPicker = useHeygenResourcePicker({
  listApi: getDigitalHumanAudioAssets,
  defaultFilters: {},
  buildParams: ({ page, pageSize }) => ({
    page,
    page_size: pageSize,
  }),
  pageSize: 12,
});

const summary = computed(() => {
  if (activeTab.value === "platform") {
    return `共 ${platformPicker.state.total} 个平台声音`;
  }
  return "";
});

watch(
  () => props.open,
  async (open) => {
    if (!open) return;
    pendingVoice.value = normalizeSelectedVoice(props.selectedVoice);
    activeTab.value = pendingVoice.value?.mode === "upload" ? "upload" : "platform";
    if (activeTab.value === "upload") {
      await initUploadTab();
      return;
    }
    await initPlatformTab();
  },
);

function normalizePlatformVoice(item) {
  if (!item?.voice_id) return null;
  return {
    ...item,
    mode: "platform",
  };
}

function normalizeUploadAudio(item) {
  if (!item?.id && !item?.audio_asset_id) return null;
  return {
    ...item,
    mode: "upload",
    audio_asset_id: item.audio_asset_id || item.id,
  };
}

function normalizeSelectedVoice(item) {
  if (!item) return null;
  if (item.mode === "upload" || item.audio_asset_id || item.audio_url) {
    return normalizeUploadAudio(item);
  }
  return normalizePlatformVoice(item);
}

async function initPlatformTab() {
  platformPicker.reset();
  const result = await platformPicker.reload();
  if (!result.ok) {
    emit("notify", result.message || "平台声音加载失败");
  }
}

async function initUploadTab() {
  uploadPicker.reset();
  const result = await uploadPicker.reload();
  if (!result.ok) {
    emit("notify", result.message || "上传音频列表加载失败");
  }
}

async function handleTabChange(value) {
  activeTab.value = value;
  if (value === "platform") {
    await initPlatformTab();
    return;
  }
  await initUploadTab();
}

async function applyFilters() {
  const result = await platformPicker.reload();
  if (!result.ok) {
    emit("notify", result.message || "平台声音加载失败");
  }
}

function handleReachEnd(event) {
  const picker = activeTab.value === "upload" ? uploadPicker : platformPicker;
  picker.handleScroll(event).then((result) => {
    if (!result.ok) {
      emit("notify", result.message || "加载失败");
    }
  });
}

function selectPlatformVoice(item) {
  pendingVoice.value = normalizePlatformVoice(item);
}

function selectUploadAudio(item) {
  pendingVoice.value = normalizeUploadAudio(item);
}

function isPlatformSelected(item) {
  return pendingVoice.value?.mode === "platform" && pendingVoice.value?.voice_id === item.voice_id;
}

function isUploadSelected(item) {
  const audioAssetId = item.audio_asset_id || item.id;
  return pendingVoice.value?.mode === "upload" && pendingVoice.value?.audio_asset_id === audioAssetId;
}

function confirmSelection() {
  if (!pendingVoice.value) {
    emit("notify", activeTab.value === "upload" ? "请选择上传音频" : "请选择平台声音");
    return;
  }
  emit("confirm", pendingVoice.value);
  emit("close");
}

function triggerFileInput() {
  fileInput.value?.click();
}

function formatDuration(seconds) {
  const totalSeconds = Math.max(0, Number(seconds || 0));
  if (!totalSeconds) return "时长未知";
  const minutes = Math.floor(totalSeconds / 60);
  const remainSeconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainSeconds).padStart(2, "0")}`;
}

function formatDateTime(value) {
  if (!value) return "刚刚上传";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "刚刚上传";
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatFileSize(size) {
  const value = Number(size || 0);
  if (value <= 0) return "";
  if (value < 1024 * 1024) {
    return `${Math.max(1, Math.round(value / 1024))} KB`;
  }
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

function readAudioDurationSeconds(file) {
  return new Promise((resolve) => {
    const objectUrl = URL.createObjectURL(file);
    const audio = new Audio();
    const cleanup = (duration = 0) => {
      URL.revokeObjectURL(objectUrl);
      resolve(Math.max(0, Math.ceil(Number(duration || 0))));
    };
    audio.preload = "metadata";
    audio.onloadedmetadata = () => cleanup(audio.duration);
    audio.onerror = () => cleanup(0);
    audio.src = objectUrl;
  });
}

function isAudioFile(file) {
  if (!file) return false;
  if (file.type.startsWith("audio/")) return true;
  return /\.(mp3|wav|m4a|aac|ogg|webm|flac)$/i.test(file.name || "");
}

async function uploadAudioFile(file) {
  if (!file) return;
  if (!isAudioFile(file)) {
    emit("notify", "请选择音频文件");
    return;
  }
  audioUploading.value = true;
  try {
    const durationSeconds = await readAudioDurationSeconds(file);
    const result = await uploadDigitalHumanAudioAsset(file, { durationSeconds });
    if (result.code !== 0) {
      emit("notify", result.message || "音频上传失败");
      return;
    }
    pendingVoice.value = normalizeUploadAudio(result.data);
    const reloadResult = await uploadPicker.reload();
    if (!reloadResult.ok) {
      emit("notify", reloadResult.message || "上传音频列表加载失败");
    }
  } catch (error) {
    emit("notify", error.response?.data?.message || "音频上传失败");
  } finally {
    audioUploading.value = false;
  }
}

function handleFileChange(event) {
  const file = Array.from(event.target.files || [])[0];
  uploadAudioFile(file);
  event.target.value = "";
}

function handleDrop(event) {
  uploadDragOver.value = false;
  const file = Array.from(event.dataTransfer.files || [])[0];
  uploadAudioFile(file);
}

async function removeAudioAsset(item) {
  if (!item?.id) return;
  if (!window.confirm("确定删除这个音频吗？")) return;
  deletingAudioId.value = item.id;
  try {
    const result = await deleteDigitalHumanAudioAsset(item.id);
    if (result.code !== 0) {
      emit("notify", result.message || "删除失败");
      return;
    }
    if (pendingVoice.value?.mode === "upload" && pendingVoice.value?.audio_asset_id === item.id) {
      pendingVoice.value = null;
    }
    const reloadResult = await uploadPicker.reload();
    if (!reloadResult.ok) {
      emit("notify", reloadResult.message || "上传音频列表加载失败");
    }
  } catch (error) {
    emit("notify", error.response?.data?.message || "删除失败，请稍后重试");
  } finally {
    deletingAudioId.value = "";
  }
}
</script>

<template>
  <HeygenPickerModalShell
    :open="open"
    title="选择声音"
    subtitle="平台声音和上传音频共用一个选择入口"
    :tabs="tabs"
    :active-tab="activeTab"
    :keyword="platformPicker.state.keyword"
    search-placeholder="搜索名称、voice_id、语言"
    :summary="summary"
    :show-toolbar="activeTab === 'platform'"
    :loading-more="activeTab === 'platform' ? platformPicker.state.loadingMore : uploadPicker.state.loadingMore"
    @close="emit('close')"
    @change-tab="handleTabChange"
    @update:keyword="platformPicker.state.keyword = $event"
    @search="applyFilters"
    @reach-end="handleReachEnd"
  >
    <template #filters>
      <div class="w-32">
        <AppSelect v-model="platformPicker.filters.language" :options="heygenVoiceLanguageOptions" @update:model-value="applyFilters" />
      </div>
      <div class="w-28">
        <AppSelect v-model="platformPicker.filters.gender" :options="heygenGenderOptions" @update:model-value="applyFilters" />
      </div>
      <div class="w-36">
        <AppSelect v-model="platformPicker.filters.support_locale" :options="heygenVoiceLocaleOptions" @update:model-value="applyFilters" />
      </div>
    </template>

    <div v-if="activeTab === 'upload'" class="space-y-4">
      <div class="rounded-2xl border border-sky-100 bg-sky-50/80 px-4 py-3">
        <p class="text-sm font-bold text-slate-800">上传 1 个音频文件作为口型驱动</p>
        <p class="mt-1 text-xs leading-relaxed text-slate-500">使用上传音频后，将不再填写口播文案，系统会直接按音频驱动数字人口型。</p>
      </div>

      <input ref="fileInput" type="file" accept="audio/*" class="hidden" @change="handleFileChange" />

      <ImageUploadSourcePanel
        :drag-over="uploadDragOver"
        action-text="上传音频"
        hint-text="支持点击上传或拖拽上传，单次只上传 1 个文件"
        :icon="UploadCloud"
        local-button-text="选择音频"
        :show-asset-button="false"
        @upload="triggerFileInput"
        @drag-over="uploadDragOver = true"
        @drag-leave="uploadDragOver = false"
        @drop="handleDrop"
      />

      <div v-if="audioUploading" class="flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-4 py-5 text-sm text-slate-500">
        <LoaderCircle class="h-4 w-4 animate-spin text-primary" />
        上传中...
      </div>

      <section class="space-y-3">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-black text-slate-800">我的音频</h3>
          <span class="text-xs text-slate-400">共 {{ uploadPicker.state.total }} 条</span>
        </div>

        <div v-if="uploadPicker.state.loading" class="flex min-h-[280px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-400">
          正在加载上传音频...
        </div>

        <div v-else-if="!uploadPicker.state.items.length" class="flex min-h-[280px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-400">
          暂无可用音频，先上传 1 个试试
        </div>

        <div v-else class="space-y-3">
          <article
            v-for="item in uploadPicker.state.items"
            :key="item.id"
            class="rounded-2xl border bg-white p-4 shadow-sm transition-all hover:border-primary/30 hover:shadow-md"
            :class="isUploadSelected(item) ? 'border-primary ring-2 ring-primary/10' : 'border-slate-200'"
            @click="selectUploadAudio(item)"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-secondary/10 text-secondary">
                    <UploadCloud class="h-4.5 w-4.5" />
                  </span>
                  <div class="min-w-0">
                    <h3 class="truncate text-sm font-black text-slate-800">{{ item.name }}</h3>
                    <p class="mt-0.5 text-xs text-slate-400">
                      {{ formatDuration(item.duration_seconds) }}<span v-if="formatFileSize(item.size)"> · {{ formatFileSize(item.size) }}</span>
                    </p>
                  </div>
                </div>

                <p class="mt-3 text-[11px] text-slate-400">上传时间：{{ formatDateTime(item.created_at) }}</p>

                <div class="mt-3" @click.stop>
                  <audio :src="item.audio_url" controls preload="none" class="h-10 w-full"></audio>
                </div>
              </div>

              <div class="flex shrink-0 flex-col items-end gap-2">
                <button
                  type="button"
                  class="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 text-slate-400 transition-colors hover:border-rose-200 hover:bg-rose-50 hover:text-rose-500"
                  :disabled="deletingAudioId === item.id"
                  title="删除音频"
                  @click.stop="removeAudioAsset(item)"
                >
                  <LoaderCircle v-if="deletingAudioId === item.id" class="h-3.5 w-3.5 animate-spin" />
                  <Trash2 v-else class="h-3.5 w-3.5" />
                </button>
                <span class="rounded-full px-2.5 py-1 text-[11px] font-bold" :class="isUploadSelected(item) ? 'bg-primary text-white' : 'bg-slate-100 text-slate-500'">
                  {{ isUploadSelected(item) ? "已选择" : "点击选择" }}
                </span>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>

    <div v-else-if="platformPicker.state.loading" class="flex min-h-[420px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-400">
      正在加载平台声音...
    </div>

    <div v-else-if="!platformPicker.state.items.length" class="flex min-h-[420px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-400">
      暂无可用平台声音
    </div>

    <div v-else class="space-y-3">
      <article
        v-for="item in platformPicker.state.items"
        :key="item.id"
        class="rounded-2xl border bg-white p-4 shadow-sm transition-all hover:border-primary/30 hover:shadow-md"
        :class="isPlatformSelected(item) ? 'border-primary ring-2 ring-primary/10' : 'border-slate-200'"
        @click="selectPlatformVoice(item)"
      >
        <div class="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div class="min-w-0">
            <div class="flex items-center gap-2">
              <span class="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-secondary/10 text-secondary">
                <Mic2 class="h-4.5 w-4.5" />
              </span>
              <div class="min-w-0">
                <h3 class="truncate text-sm font-black text-slate-800">{{ item.name }}</h3>
                <p class="mt-0.5 truncate text-xs text-slate-400">{{ item.voice_id }}</p>
              </div>
            </div>

            <div class="mt-3 flex flex-wrap gap-2">
              <span class="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-500">{{ item.language || "未标注语言" }}</span>
              <span class="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-500">{{ item.gender === "unknown" || !item.gender ? "未知性别" : item.gender }}</span>
              <span class="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-500">Locale {{ item.support_locale ? "支持" : "不支持" }}</span>
              <span class="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-500">Pause {{ item.support_pause ? "支持" : "不支持" }}</span>
            </div>
          </div>

          <div class="flex flex-col items-start gap-3 lg:items-end">
            <div class="max-w-full" @click.stop>
              <audio v-if="item.preview_audio_url" :src="item.preview_audio_url" controls preload="none" class="h-8 w-64 max-w-full"></audio>
              <span v-else class="text-xs text-slate-400">暂无试听</span>
            </div>
            <span class="rounded-full px-2.5 py-1 text-[11px] font-bold" :class="isPlatformSelected(item) ? 'bg-primary text-white' : 'bg-slate-100 text-slate-500'">
              {{ isPlatformSelected(item) ? "已选择" : "点击选择" }}
            </span>
          </div>
        </div>
      </article>
    </div>

    <template #footer>
      <div class="flex items-center justify-between gap-3">
        <p class="text-xs text-slate-400">{{ pendingVoice?.name ? `已选：${pendingVoice.name}` : "请选择 1 个声音或音频" }}</p>
        <div class="flex items-center gap-2">
          <button type="button" class="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50" @click="emit('close')">取消</button>
          <button type="button" class="rounded-xl bg-primary px-4 py-2 text-xs font-bold text-white transition-colors hover:bg-secondary" @click="confirmSelection">确认选择</button>
        </div>
      </div>
    </template>
  </HeygenPickerModalShell>
</template>
