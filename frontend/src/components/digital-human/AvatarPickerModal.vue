<script setup>
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { LoaderCircle, PlayCircle, Trash2, UploadCloud } from "lucide-vue-next";
import {
  deletePhotoAvatar,
  deletePhotoAvatarTask,
  getDigitalHumanAvatars,
  getPhotoAvatarTasks,
  getPhotoAvatars,
  pollPhotoAvatarTask,
  uploadPhotoAvatar,
} from "@/api/digitalHuman.js";
import HeygenPickerModalShell from "@/components/digital-human/HeygenPickerModalShell.vue";
import ImageUploadSourcePanel from "@/components/generation/image/ImageUploadSourcePanel.vue";
import AppModal from "@/components/ui/AppModal.vue";
import AppSelect from "@/components/ui/AppSelect.vue";
import { useHeygenResourcePicker } from "@/composables/digital-human/useHeygenResourcePicker.js";
import { useDigitalHumanPricing } from "@/composables/digital-human/useDigitalHumanPricing.js";
import {
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
  { value: "photo", label: "照片数字人" },
];
const avatarGenderOptions = heygenGenderOptions.filter((item) => item.value !== "unknown");
const PHOTO_TASK_POLL_INTERVAL_MS = 5000;

const activeTab = ref("system");
const pendingAvatar = ref(null);
const previewItem = ref(null);
const fileInput = ref(null);
const uploadDragOver = ref(false);
const creatingPhotoAvatar = ref(false);
const deletingTaskId = ref("");
const deletingAssetId = ref("");
const photoAvatarName = ref("");
const photoFile = ref(null);
const photoPreviewUrl = ref("");
let photoTaskPollTimer = null;

const pricing = useDigitalHumanPricing();

const systemPicker = useHeygenResourcePicker({
  listApi: getDigitalHumanAvatars,
  defaultFilters: {
    gender: "",
    orientation: "",
  },
  buildParams: ({ page, pageSize, keyword, filters }) => ({
    page,
    page_size: pageSize,
    keyword: keyword || undefined,
    gender: filters.gender || undefined,
    orientation: filters.orientation || undefined,
  }),
});

const photoAvatarPicker = useHeygenResourcePicker({
  listApi: getPhotoAvatars,
  defaultFilters: {},
  buildParams: ({ page, pageSize }) => ({
    page,
    page_size: pageSize,
  }),
  pageSize: 12,
});

const photoTaskPicker = useHeygenResourcePicker({
  listApi: getPhotoAvatarTasks,
  defaultFilters: {},
  buildParams: ({ page, pageSize }) => ({
    page,
    page_size: pageSize,
  }),
  pageSize: 12,
});

const summary = computed(() => {
  if (activeTab.value === "system") {
    return `共 ${systemPicker.state.total} 个系统数字人`;
  }
  return `共 ${photoAvatarPicker.state.total} 个照片数字人`;
});

const photoTaskItems = computed(() =>
  photoTaskPicker.state.items.filter(
    (item) => item.status !== "done" || !item.result_avatar_id,
  ),
);

const photoCreateCost = computed(
  () => Number(pricing.photoAvatarCreateCost.value || 2000),
);

watch(
  () => props.open,
  async (open) => {
    if (!open) {
      stopPhotoTaskPolling();
      previewItem.value = null;
      resetPhotoUploadState();
      return;
    }
    pendingAvatar.value = normalizeAvatar(props.selectedAvatar);
    activeTab.value = pendingAvatar.value?.source === "photo" ? "photo" : "system";
    await pricing.loadPricing();
    if (activeTab.value === "photo") {
      await initPhotoTab();
    } else {
      await initSystemTab();
    }
  },
);

watch(
  () => [props.open, activeTab.value, photoTaskItems.value.length],
  () => {
    if (!props.open || activeTab.value !== "photo") {
      stopPhotoTaskPolling();
      return;
    }
    startPhotoTaskPolling();
  },
);

onBeforeUnmount(() => {
  stopPhotoTaskPolling();
  clearPhotoPreviewUrl();
});

function notify(type, message) {
  emit("notify", { type, message });
}

function notifyError(message) {
  notify("error", message);
}

function normalizeAvatar(item) {
  if (!item?.avatar_id) return null;
  return {
    ...item,
    source: item.source || "system",
    asset_id: item.asset_id || "",
    avatar_type: item.avatar_type || "studio_avatar",
  };
}

function formatDateTime(value) {
  if (!value) return "刚刚创建";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "刚刚创建";
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function stopPhotoTaskPolling() {
  if (photoTaskPollTimer) {
    window.clearInterval(photoTaskPollTimer);
    photoTaskPollTimer = null;
  }
}

function startPhotoTaskPolling() {
  stopPhotoTaskPolling();
  if (!photoTaskItems.value.length) return;
  photoTaskPollTimer = window.setInterval(() => {
    pollRunningPhotoTasks();
  }, PHOTO_TASK_POLL_INTERVAL_MS);
}

async function pollRunningPhotoTasks() {
  const runningTasks = photoTaskItems.value.filter((item) =>
    ["pending", "processing"].includes(item.status),
  );
  if (!runningTasks.length) {
    stopPhotoTaskPolling();
    return;
  }
  try {
    await Promise.all(
      runningTasks.map(async (item) => {
        const result = await pollPhotoAvatarTask(item.id);
        if (result.code !== 0) {
          throw new Error(result.message || "照片数字人状态查询失败");
        }
      }),
    );
    await reloadPhotoLists();
  } catch (error) {
    notifyError(error.message || "照片数字人状态查询失败");
    stopPhotoTaskPolling();
  }
}

function clearPhotoPreviewUrl() {
  if (photoPreviewUrl.value) {
    URL.revokeObjectURL(photoPreviewUrl.value);
    photoPreviewUrl.value = "";
  }
}

function resetPhotoUploadState() {
  photoAvatarName.value = "";
  photoFile.value = null;
  uploadDragOver.value = false;
  clearPhotoPreviewUrl();
}

function setPhotoFile(file) {
  if (!file) return;
  photoFile.value = file;
  if (!photoAvatarName.value.trim()) {
    photoAvatarName.value = (file.name || "").replace(/\.[^/.]+$/, "").trim().slice(0, 120);
  }
  clearPhotoPreviewUrl();
  photoPreviewUrl.value = URL.createObjectURL(file);
}

function triggerFileInput() {
  fileInput.value?.click();
}

function isImageFile(file) {
  if (!file) return false;
  if (file.type.startsWith("image/")) return true;
  return /\.(jpg|jpeg|png|webp|gif)$/i.test(file.name || "");
}

function handleFileChange(event) {
  const file = Array.from(event.target.files || [])[0];
  if (file) {
    handleSelectedFile(file);
  }
  event.target.value = "";
}

function handleSelectedFile(file) {
  if (!isImageFile(file)) {
    notifyError("请选择图片文件");
    return;
  }
  setPhotoFile(file);
}

function handleDrop(event) {
  uploadDragOver.value = false;
  const file = Array.from(event.dataTransfer.files || [])[0];
  if (file) {
    handleSelectedFile(file);
  }
}

async function initSystemTab() {
  stopPhotoTaskPolling();
  systemPicker.reset();
  const result = await systemPicker.reload();
  if (!result.ok) {
    notifyError(result.message || "系统数字人加载失败");
  }
}

async function reloadPhotoLists() {
  const [avatarResult, taskResult] = await Promise.all([
    photoAvatarPicker.reload(),
    photoTaskPicker.reload(),
  ]);
  if (!avatarResult.ok) {
    notifyError(avatarResult.message || "照片数字人加载失败");
  }
  if (!taskResult.ok) {
    notifyError(taskResult.message || "照片数字人任务加载失败");
  }
}

async function initPhotoTab() {
  photoAvatarPicker.reset();
  photoTaskPicker.reset();
  await reloadPhotoLists();
}

async function handleTabChange(value) {
  activeTab.value = value;
  if (value === "photo") {
    await initPhotoTab();
    return;
  }
  await initSystemTab();
}

async function applyFilters() {
  const result = await systemPicker.reload();
  if (!result.ok) {
    notifyError(result.message || "系统数字人加载失败");
  }
}

async function handleReachEnd(event) {
  if (activeTab.value === "photo") {
    const [taskResult, avatarResult] = await Promise.all([
      photoTaskPicker.handleScroll(event),
      photoAvatarPicker.handleScroll(event),
    ]);
    if (!taskResult.ok) {
      notifyError(taskResult.message || "照片数字人任务加载失败");
    }
    if (!avatarResult.ok) {
      notifyError(avatarResult.message || "照片数字人加载失败");
    }
    return;
  }
  const result = await systemPicker.handleScroll(event);
  if (!result.ok) {
    notifyError(result.message || "系统数字人加载失败");
  }
}

function selectAvatar(item) {
  pendingAvatar.value = normalizeAvatar(item);
}

function isSelected(item) {
  const next = normalizeAvatar(item);
  if (!pendingAvatar.value || !next) return false;
  if (pendingAvatar.value.source === "photo" || next.source === "photo") {
    if (pendingAvatar.value.asset_id && next.asset_id) {
      return pendingAvatar.value.asset_id === next.asset_id;
    }
    return pendingAvatar.value.avatar_id === next.avatar_id;
  }
  return pendingAvatar.value.avatar_id === next.avatar_id;
}

function confirmSelection() {
  if (!pendingAvatar.value) {
    notifyError("请选择数字人");
    return;
  }
  emit("confirm", pendingAvatar.value);
  emit("close");
}

async function createPhotoAvatarAction() {
  const name = photoAvatarName.value.trim();
  if (!photoFile.value) {
    notifyError("请先上传 1 张照片");
    return;
  }
  if (!name) {
    notifyError("请输入数字人名称");
    return;
  }
  creatingPhotoAvatar.value = true;
  try {
    const result = await uploadPhotoAvatar({
      file: photoFile.value,
      name,
    });
    if (result.code !== 0) {
      notifyError(result.message || "照片数字人创建失败");
      return;
    }
    resetPhotoUploadState();
    await reloadPhotoLists();
    if (result.data?.status === "done" && result.data?.result_avatar_id) {
      const matched = photoAvatarPicker.state.items.find(
        (item) => item.id === result.data.result_avatar_id,
      );
      if (matched) {
        pendingAvatar.value = normalizeAvatar(matched);
      }
    }
  } catch (error) {
    const detail = error.response?.data?.detail;
    const detailMessage = Array.isArray(detail)
      ? detail.map((item) => item?.msg).filter(Boolean).join("，")
      : "";
    notifyError(error.response?.data?.message || detailMessage || "照片数字人创建失败");
  } finally {
    creatingPhotoAvatar.value = false;
  }
}

async function deletePhotoAvatarAction(item) {
  if (!item?.id) return;
  if (!window.confirm("确定删除这个照片数字人吗？删除后不会影响历史任务快照。")) return;
  deletingAssetId.value = item.id;
  try {
    const result = await deletePhotoAvatar(item.id);
    if (result.code !== 0) {
      notifyError(result.message || "删除失败");
      return;
    }
    if (pendingAvatar.value?.source === "photo" && pendingAvatar.value?.asset_id === item.id) {
      pendingAvatar.value = null;
    }
    await reloadPhotoLists();
  } catch (error) {
    notifyError(error.response?.data?.message || "删除失败，请稍后重试");
  } finally {
    deletingAssetId.value = "";
  }
}

async function deletePhotoAvatarTaskAction(item) {
  if (!item?.id || item.status !== "failed") return;
  if (!window.confirm("确定删除这条失败任务吗？删除后将不再显示。")) return;
  deletingTaskId.value = item.id;
  try {
    const result = await deletePhotoAvatarTask(item.id);
    if (result.code !== 0) {
      notifyError(result.message || "删除失败");
      return;
    }
    await reloadPhotoLists();
  } catch (error) {
    notifyError(error.response?.data?.message || "删除失败，请稍后重试");
  } finally {
    deletingTaskId.value = "";
  }
}

function photoTaskStatusText(status) {
  if (status === "processing") return "创建中";
  if (status === "failed") return "创建失败";
  if (status === "done") return "已完成";
  return "排队中";
}

function photoTaskStatusClass(status) {
  if (status === "processing") return "bg-amber-100 text-amber-700";
  if (status === "failed") return "bg-rose-100 text-rose-600";
  if (status === "done") return "bg-emerald-100 text-emerald-700";
  return "bg-slate-100 text-slate-500";
}
</script>

<template>
  <HeygenPickerModalShell
    :open="open"
    title="选择数字人"
    subtitle=""
    :tabs="tabs"
    :active-tab="activeTab"
    :keyword="systemPicker.state.keyword"
    search-placeholder="搜索名称、avatar_id、group_id"
    :summary="summary"
    :show-toolbar="activeTab === 'system'"
    :loading-more="activeTab === 'system' ? systemPicker.state.loadingMore : photoAvatarPicker.state.loadingMore || photoTaskPicker.state.loadingMore"
    @close="emit('close')"
    @change-tab="handleTabChange"
    @update:keyword="systemPicker.state.keyword = $event"
    @search="applyFilters"
    @reach-end="handleReachEnd"
  >
    <template #filters>
      <div class="w-28">
        <AppSelect v-model="systemPicker.filters.gender" :options="avatarGenderOptions" @update:model-value="applyFilters" />
      </div>
      <div class="w-28">
        <AppSelect v-model="systemPicker.filters.orientation" :options="heygenAvatarOrientationOptions" @update:model-value="applyFilters" />
      </div>
    </template>

    <div v-if="activeTab === 'photo'" class="space-y-4">
      <div class="rounded-2xl border border-sky-100 bg-sky-50/80 px-4 py-3">
        <p class="text-sm font-bold text-slate-800">上传 1 张清晰正面人像图</p>
        <p class="mt-1 text-xs leading-relaxed text-slate-500">创建成功后可在数字人口播中重复使用。本次创建将消耗 {{ photoCreateCost }} 积分，失败自动退回。</p>
      </div>

      <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="handleFileChange" />

      <ImageUploadSourcePanel
        :drag-over="uploadDragOver"
        action-text="上传人物照片"
        hint-text="支持点击上传或拖拽上传，单次只上传 1 张图片"
        :icon="UploadCloud"
        local-button-text="选择照片"
        :show-asset-button="false"
        @upload="triggerFileInput"
        @drag-over="uploadDragOver = true"
        @drag-leave="uploadDragOver = false"
        @drop="handleDrop"
      />

      <div v-if="photoPreviewUrl || photoAvatarName" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div class="grid gap-4 lg:grid-cols-[180px_1fr]">
          <div class="overflow-hidden rounded-2xl bg-slate-100">
            <img v-if="photoPreviewUrl" :src="photoPreviewUrl" class="aspect-[4/5] w-full object-cover" alt="照片预览" />
            <div v-else class="flex aspect-[4/5] items-center justify-center text-xs text-slate-400">待上传照片</div>
          </div>
          <div class="space-y-4">
            <label class="block">
              <span class="mb-1.5 block text-xs font-bold text-slate-700">数字人名称</span>
              <input
                v-model="photoAvatarName"
                type="text"
                maxlength="120"
                class="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-800 outline-none transition-colors focus:border-primary focus:ring-1 focus:ring-primary"
                placeholder="输入名称，方便后续选择"
              />
            </label>

            <div class="flex items-center justify-between gap-3">
              <button
                type="button"
                class="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50"
                @click="resetPhotoUploadState"
              >
                清空
              </button>
              <button
                type="button"
                class="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-xs font-bold text-white transition-colors hover:bg-secondary disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="creatingPhotoAvatar"
                @click="createPhotoAvatarAction"
              >
                <LoaderCircle v-if="creatingPhotoAvatar" class="h-4 w-4 animate-spin" />
                <span>{{ creatingPhotoAvatar ? "创建中..." : "创建照片数字人" }}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <section v-if="photoTaskItems.length" class="space-y-3">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-black text-slate-800">创建任务</h3>
          <span class="text-xs text-slate-400">共 {{ photoTaskPicker.state.total }} 条</span>
        </div>

        <article
          v-for="item in photoTaskItems"
          :key="item.id"
          class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
        >
          <div class="flex items-start gap-4">
            <div class="relative w-24 shrink-0 overflow-hidden rounded-2xl bg-slate-100">
              <img v-if="item.preview_image_url" :src="item.preview_image_url" class="aspect-[4/5] w-full object-cover" alt="照片数字人任务预览" />
              <div v-else class="flex aspect-[4/5] items-center justify-center text-xs text-slate-400">无预览图</div>
              <button
                v-if="item.preview_image_url || item.preview_video_url"
                type="button"
                class="absolute right-2 top-2 rounded-full bg-white/90 p-1 text-slate-600 shadow-sm hover:text-primary"
                @click="previewItem = item"
              >
                <PlayCircle class="h-4 w-4" />
              </button>
            </div>

            <div class="min-w-0 flex-1">
              <div class="flex flex-wrap items-center gap-2">
                <h4 class="truncate text-sm font-black text-slate-800">{{ item.name }}</h4>
                <span class="rounded-full px-2.5 py-1 text-[11px] font-bold" :class="photoTaskStatusClass(item.status)">
                  {{ photoTaskStatusText(item.status) }}
                </span>
              </div>
              <p class="mt-2 text-xs text-slate-400">创建时间：{{ formatDateTime(item.created_at) }}</p>
              <p v-if="item.error_message" class="mt-2 text-xs text-rose-500">{{ item.error_message }}</p>
            </div>

            <button
              v-if="item.status === 'failed'"
              type="button"
              class="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-slate-200 text-slate-400 transition-colors hover:border-rose-200 hover:bg-rose-50 hover:text-rose-500"
              :disabled="deletingTaskId === item.id"
              title="删除失败任务"
              @click="deletePhotoAvatarTaskAction(item)"
            >
              <LoaderCircle v-if="deletingTaskId === item.id" class="h-3.5 w-3.5 animate-spin" />
              <Trash2 v-else class="h-3.5 w-3.5" />
            </button>
          </div>
        </article>
      </section>

      <section class="space-y-3">
        <div class="flex items-center justify-between">
          <h3 class="text-sm font-black text-slate-800">我的照片数字人</h3>
          <span class="text-xs text-slate-400">共 {{ photoAvatarPicker.state.total }} 个</span>
        </div>

        <div v-if="photoAvatarPicker.state.loading" class="flex min-h-[280px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-400">
          正在加载照片数字人...
        </div>

        <div v-else-if="!photoAvatarPicker.state.items.length" class="flex min-h-[280px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-400">
          暂无可用照片数字人，先上传 1 张试试
        </div>

        <div v-else class="space-y-3">
          <article
            v-for="item in photoAvatarPicker.state.items"
            :key="item.id"
            class="rounded-2xl border bg-white p-4 shadow-sm transition-all hover:border-primary/30 hover:shadow-md"
            :class="isSelected(item) ? 'border-primary ring-2 ring-primary/10' : 'border-slate-200'"
            @click="selectAvatar(item)"
          >
            <div class="flex items-start gap-4">
              <div class="relative w-24 shrink-0 overflow-hidden rounded-2xl bg-slate-100">
                <img v-if="item.preview_image_url" :src="item.preview_image_url" class="aspect-[4/5] w-full object-cover" alt="照片数字人预览" />
                <div v-else class="flex aspect-[4/5] items-center justify-center text-xs text-slate-400">无预览图</div>
                <button
                  v-if="item.preview_image_url || item.preview_video_url"
                  type="button"
                  class="absolute right-2 top-2 rounded-full bg-white/90 p-1 text-slate-600 shadow-sm hover:text-primary"
                  @click.stop="previewItem = item"
                >
                  <PlayCircle class="h-4 w-4" />
                </button>
              </div>

              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <h4 class="truncate text-sm font-black text-slate-800">{{ item.name }}</h4>
                  <span class="rounded-full px-2.5 py-1 text-[11px] font-bold" :class="isSelected(item) ? 'bg-primary text-white' : 'bg-slate-100 text-slate-500'">
                    {{ isSelected(item) ? "已选择" : "点击选择" }}
                  </span>
                </div>
                <p class="mt-2 truncate text-xs text-slate-400">avatar_id：{{ item.avatar_id }}</p>
                <p class="mt-1 text-xs text-slate-400">创建时间：{{ formatDateTime(item.created_at) }}</p>
              </div>

              <button
                type="button"
                class="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-slate-200 text-slate-400 transition-colors hover:border-rose-200 hover:bg-rose-50 hover:text-rose-500"
                :disabled="deletingAssetId === item.id"
                title="删除照片数字人"
                @click.stop="deletePhotoAvatarAction(item)"
              >
                <LoaderCircle v-if="deletingAssetId === item.id" class="h-3.5 w-3.5 animate-spin" />
                <Trash2 v-else class="h-3.5 w-3.5" />
              </button>
            </div>
          </article>
        </div>
      </section>
    </div>

    <div v-else-if="systemPicker.state.loading" class="flex min-h-[420px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-400">
      正在加载系统数字人...
    </div>

    <div v-else-if="!systemPicker.state.items.length" class="flex min-h-[420px] items-center justify-center rounded-2xl border border-slate-200 bg-white text-sm text-slate-400">
      暂无可用系统数字人
    </div>

    <div v-else class="grid gap-4 md:grid-cols-3 xl:grid-cols-4">
      <article
        v-for="item in systemPicker.state.items"
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
          <div class="flex items-center justify-between gap-2 pt-1">
            <button
              v-if="item.preview_video_url || item.preview_image_url"
              type="button"
              class="inline-flex items-center gap-1.5 rounded-xl bg-primary/10 px-3 py-2 text-xs font-bold text-primary transition-colors hover:bg-primary/15 hover:text-secondary"
              @click.stop="previewItem = item"
            >
              <PlayCircle class="h-4 w-4" />
              预览
            </button>
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
