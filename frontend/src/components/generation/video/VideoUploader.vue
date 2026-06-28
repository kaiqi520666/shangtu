<script setup>
import { computed, onBeforeUnmount, ref } from "vue";
import { LoaderCircle, Trash2, Video } from "lucide-vue-next";
import { uploadVideo } from "@/api/video.js";
import AssetPickerModal from "@/components/assets/AssetPickerModal.vue";
import ImageUploadSourcePanel from "@/components/generation/image/ImageUploadSourcePanel.vue";

const props = defineProps({
  video: {
    type: Object,
    default: null,
  },
  title: {
    type: String,
    default: "参考视频",
  },
  addText: {
    type: String,
    default: "添加参考视频",
  },
  hintText: {
    type: String,
    default: "必须选择 1 条视频",
  },
});

const emit = defineEmits(["update:video", "notify"]);

const fileInput = ref(null);
const dragOver = ref(false);
const assetPickerOpen = ref(false);
const localPreviewUrl = ref("");

const videoUrl = computed(() => props.video?.url || props.video?.previewUrl || "");
const selectedLabel = computed(() => {
  if (!props.video) return "";
  if (props.video.uploading) return "视频上传中...";
  if (props.video.source === "asset") return "来自资产库";
  return "本地上传";
});

function triggerFileInput() {
  fileInput.value?.click();
}

function openAssetPicker() {
  assetPickerOpen.value = true;
}

function makeLocalVideo(file) {
  releaseLocalPreview();
  localPreviewUrl.value = URL.createObjectURL(file);
  return {
    id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    previewUrl: localPreviewUrl.value,
    url: "",
    objectKey: "",
    contentType: file.type,
    size: file.size,
    uploading: true,
    error: "",
    source: "upload",
  };
}

function releaseLocalPreview() {
  if (!localPreviewUrl.value) return;
  URL.revokeObjectURL(localPreviewUrl.value);
  localPreviewUrl.value = "";
}

async function uploadSelectedFile(file) {
  if (!file.type.startsWith("video/")) {
    emit("notify", "请选择视频文件");
    return;
  }
  const placeholder = makeLocalVideo(file);
  emit("update:video", placeholder);
  try {
    const result = await uploadVideo(file);
    if (result.code !== 0) {
      emit("update:video", { ...placeholder, uploading: false, error: result.message || "视频上传失败" });
      emit("notify", result.message || "视频上传失败");
      return;
    }
    emit("update:video", {
      ...placeholder,
      uploading: false,
      error: "",
      url: result.data.url,
      objectKey: result.data.object_key,
      contentType: result.data.content_type,
      size: result.data.size,
    });
  } catch (error) {
    emit("update:video", { ...placeholder, uploading: false, error: "视频上传失败" });
    emit("notify", error.response?.data?.message || "视频上传失败");
  }
}

function handleFileChange(event) {
  const file = Array.from(event.target.files || [])[0];
  if (file) uploadSelectedFile(file);
  event.target.value = "";
}

function handleDrop(event) {
  dragOver.value = false;
  const file = Array.from(event.dataTransfer.files || [])[0];
  if (file) uploadSelectedFile(file);
}

function addAssetVideo(assets) {
  const asset = assets[0];
  if (!asset?.url) return;
  releaseLocalPreview();
  emit("update:video", {
    id: `asset_${asset.taskId || asset.id}`,
    previewUrl: asset.url,
    url: asset.url,
    objectKey: "",
    contentType: "",
    size: 0,
    uploading: false,
    error: "",
    source: "asset",
    assetTaskId: asset.taskId || asset.id,
  });
  assetPickerOpen.value = false;
}

function clearVideo() {
  releaseLocalPreview();
  emit("update:video", null);
}

onBeforeUnmount(() => {
  releaseLocalPreview();
});
</script>

<template>
  <section class="border-b border-slate-100 bg-slate-50/40 p-5">
    <div class="mb-3 flex items-center justify-between">
      <label class="flex items-center gap-1.5 text-xs font-bold text-slate-700">
        <span class="h-1.5 w-1.5 rounded-full bg-primary"></span>
        {{ title }}
      </label>
      <button
        v-if="video"
        type="button"
        class="text-xs text-slate-400 transition-colors hover:text-rose-500"
        @click="clearVideo"
      >
        清空
      </button>
    </div>

    <input ref="fileInput" type="file" accept="video/*" class="hidden" @change="handleFileChange" />

    <ImageUploadSourcePanel
      v-if="!video"
      :action-text="addText"
      :hint-text="hintText"
      :drag-over="dragOver"
      :icon="Video"
      local-button-text="本地上传"
      asset-button-text="资产库选择"
      @upload="triggerFileInput"
      @asset="openAssetPicker"
      @drag-over="dragOver = true"
      @drag-leave="dragOver = false"
      @drop="handleDrop"
    />

    <div v-else class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div class="relative aspect-video bg-slate-900">
        <video
          v-if="videoUrl"
          :src="videoUrl"
          class="h-full w-full object-contain"
          controls
          muted
          playsinline
          preload="metadata"
        ></video>
        <div
          v-if="video.uploading"
          class="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-white/75 text-xs font-semibold text-primary"
        >
          <LoaderCircle class="h-5 w-5 animate-spin" />
          上传中...
        </div>
        <div
          v-else-if="video.error"
          class="absolute inset-x-0 bottom-0 bg-rose-500/90 px-3 py-2 text-center text-xs font-bold text-white"
        >
          {{ video.error }}
        </div>
      </div>
      <div class="flex items-center justify-between gap-3 px-3 py-2">
        <span class="truncate text-xs font-semibold text-slate-500">{{ selectedLabel }}</span>
        <button
          type="button"
          class="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-slate-200 text-rose-500 transition-colors hover:bg-rose-50"
          title="删除参考视频"
          @click="clearVideo"
        >
          <Trash2 class="h-3.5 w-3.5" />
        </button>
      </div>
    </div>

    <AssetPickerModal
      :open="assetPickerOpen"
      media-type="video"
      title="从资产库选择视频"
      :max-count="1"
      :exclude-urls="videoUrl ? [videoUrl] : []"
      @close="assetPickerOpen = false"
      @confirm="addAssetVideo"
      @notify="emit('notify', $event)"
    />
  </section>
</template>
