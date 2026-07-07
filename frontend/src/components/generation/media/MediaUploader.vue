<script setup>
import { computed, nextTick, onBeforeUnmount, ref } from "vue";
import { FileAudio, LoaderCircle, Trash2, Video } from "lucide-vue-next";
import { uploadAudio, uploadVideo } from "@/api/video.js";
import AssetPickerModal from "@/components/assets/AssetPickerModal.vue";
import ImageUploadSourcePanel from "@/components/generation/image/ImageUploadSourcePanel.vue";

const props = defineProps({
  items: {
    type: Array,
    required: true,
  },
  mediaType: {
    type: String,
    required: true,
    validator: (value) => ["video", "audio"].includes(value),
  },
  title: {
    type: String,
    required: true,
  },
  addText: {
    type: String,
    required: true,
  },
  hintText: {
    type: String,
    required: true,
  },
  maxCount: {
    type: Number,
    default: 1,
  },
  limitMessage: {
    type: String,
    default: "素材数量已达上限",
  },
  showAssetButton: {
    type: Boolean,
    default: true,
  },
});

const emit = defineEmits(["update:items", "notify"]);

const fileInput = ref(null);
const dragOver = ref(false);
const assetPickerOpen = ref(false);

const icon = computed(() => (props.mediaType === "audio" ? FileAudio : Video));
const accept = computed(() => `${props.mediaType}/*`);
const remainingCount = computed(() => Math.max(0, props.maxCount - props.items.length));
const canPickAsset = computed(() => props.showAssetButton);

function triggerFileInput() {
  fileInput.value?.click();
}

function openAssetPicker() {
  if (!canPickAsset.value) return;
  if (remainingCount.value <= 0) {
    emit("notify", props.limitMessage);
    return;
  }
  assetPickerOpen.value = true;
}

function makeLocalItem(file, index) {
  return {
    id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}_${index}`,
    previewUrl: URL.createObjectURL(file),
    url: "",
    objectKey: "",
    contentType: file.type,
    size: file.size,
    name: file.name || "",
    uploading: true,
    error: "",
    source: "upload",
  };
}

function patchItem(id, patch) {
  emit(
    "update:items",
    props.items.map((item) => (item.id === id ? { ...item, ...patch } : item)),
  );
}

async function uploadItem(file, item) {
  try {
    const result = await (props.mediaType === "audio" ? uploadAudio(file) : uploadVideo(file));
    if (result.code !== 0) {
      patchItem(item.id, { uploading: false, error: result.message || "素材上传失败" });
      emit("notify", result.message || "素材上传失败");
      return;
    }
    patchItem(item.id, {
      uploading: false,
      error: "",
      url: result.data.url,
      objectKey: result.data.object_key,
      contentType: result.data.content_type,
      size: result.data.size,
    });
  } catch (error) {
    patchItem(item.id, { uploading: false, error: "素材上传失败" });
    emit("notify", error.response?.data?.message || "素材上传失败");
  }
}

async function processFiles(files) {
  const matchedFiles = files.filter((file) => file.type.startsWith(`${props.mediaType}/`));
  if (remainingCount.value <= 0) {
    emit("notify", props.limitMessage);
    return;
  }

  const selected = matchedFiles.slice(0, remainingCount.value);
  if (matchedFiles.length > selected.length) {
    emit("notify", `已达到 ${props.maxCount} 个上限，多余素材未添加`);
  }
  if (selected.length === 0) return;

  const placeholders = selected.map(makeLocalItem);
  emit("update:items", [...props.items, ...placeholders]);
  await nextTick();
  await Promise.all(selected.map((file, index) => uploadItem(file, placeholders[index])));
}

function handleFileChange(event) {
  processFiles(Array.from(event.target.files || []));
  event.target.value = "";
}

function handleDrop(event) {
  dragOver.value = false;
  processFiles(Array.from(event.dataTransfer.files || []));
}

function addAssetItems(assets) {
  const fallbackName = props.mediaType === "audio" ? "资产库音频" : "资产库视频";
  const selected = assets.slice(0, remainingCount.value).map((asset) => ({
    id: `asset_${asset.taskId || asset.id}`,
    previewUrl: asset.url,
    url: asset.url,
    objectKey: "",
    contentType: "",
    size: 0,
    name: asset.title || fallbackName,
    uploading: false,
    error: "",
    source: "asset",
    assetTaskId: asset.taskId || asset.id,
  }));
  emit("update:items", [...props.items, ...selected]);
  assetPickerOpen.value = false;
}

function removeItem(index) {
  const item = props.items[index];
  if (item?.previewUrl?.startsWith("blob:")) URL.revokeObjectURL(item.previewUrl);
  emit("update:items", props.items.filter((_, itemIndex) => itemIndex !== index));
}

function clearItems() {
  props.items.forEach((item) => {
    if (item?.previewUrl?.startsWith("blob:")) URL.revokeObjectURL(item.previewUrl);
  });
  emit("update:items", []);
}

onBeforeUnmount(() => {
  props.items.forEach((item) => {
    if (item?.previewUrl?.startsWith("blob:")) URL.revokeObjectURL(item.previewUrl);
  });
});
</script>

<template>
  <section class="border-b border-slate-100 bg-slate-50/40 p-5">
    <div class="mb-3 flex items-center justify-between">
      <label class="flex items-center gap-1.5 text-xs font-bold text-slate-700">
        <span class="h-1.5 w-1.5 rounded-full bg-primary"></span>
        {{ title }}
        <span class="font-normal text-slate-400">(已选 {{ items.length }}/{{ maxCount }})</span>
      </label>
      <button
        v-if="items.length > 0"
        type="button"
        class="text-xs text-slate-400 transition-colors hover:text-rose-500"
        @click="clearItems"
      >
        清空
      </button>
    </div>

    <input ref="fileInput" type="file" :accept="accept" class="hidden" multiple @change="handleFileChange" />

    <ImageUploadSourcePanel
      v-if="items.length === 0"
      :action-text="addText"
      :hint-text="hintText"
      :drag-over="dragOver"
      :icon="icon"
      :show-asset-button="canPickAsset"
      local-button-text="本地上传"
      asset-button-text="资产库选择"
      @upload="triggerFileInput"
      @asset="openAssetPicker"
      @drag-over="dragOver = true"
      @drag-leave="dragOver = false"
      @drop="handleDrop"
    />

    <div v-else class="space-y-3">
      <div class="grid gap-3">
        <div
          v-for="(item, index) in items"
          :key="item.id || item.url || index"
          class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm"
        >
          <div v-if="mediaType === 'video'" class="relative aspect-video bg-slate-900">
            <video
              v-if="item.url || item.previewUrl"
              :src="item.url || item.previewUrl"
              class="h-full w-full object-contain"
              controls
              muted
              playsinline
              preload="metadata"
            ></video>
            <div
              v-if="item.uploading"
              class="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-white/75 text-xs font-semibold text-primary"
            >
              <LoaderCircle class="h-5 w-5 animate-spin" />
              上传中...
            </div>
          </div>

          <div v-else class="flex items-center gap-3 bg-slate-50 px-3 py-3">
            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white text-primary shadow-sm">
              <FileAudio class="h-5 w-5" />
            </div>
            <audio v-if="item.url || item.previewUrl" :src="item.url || item.previewUrl" controls preload="none" class="h-10 min-w-0 flex-1"></audio>
            <span v-else class="text-xs font-semibold text-slate-500">音频上传中...</span>
          </div>

          <div class="flex items-center justify-between gap-3 px-3 py-2">
            <span class="truncate text-xs font-semibold text-slate-500">
              {{ item.uploading ? "上传中..." : item.name || (item.source === "asset" ? "来自资产库" : "本地上传") }}
            </span>
            <button
              type="button"
              class="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-slate-200 text-rose-500 transition-colors hover:bg-rose-50"
              title="删除素材"
              @click="removeItem(index)"
            >
              <Trash2 class="h-3.5 w-3.5" />
            </button>
          </div>
          <p v-if="item.error" class="bg-rose-500 px-3 py-2 text-center text-xs font-bold text-white">{{ item.error }}</p>
        </div>
      </div>

      <ImageUploadSourcePanel
        v-if="items.length < maxCount"
        :action-text="addText"
        :hint-text="hintText"
        :drag-over="dragOver"
        :icon="icon"
        :show-asset-button="canPickAsset"
        local-button-text="继续上传"
        asset-button-text="资产库选择"
        @upload="triggerFileInput"
        @asset="openAssetPicker"
        @drag-over="dragOver = true"
        @drag-leave="dragOver = false"
        @drop="handleDrop"
      />
    </div>

    <AssetPickerModal
      :open="assetPickerOpen"
      :media-type="mediaType"
      :title="`从资产库选择${mediaType === 'audio' ? '音频' : '视频'}`"
      :max-count="remainingCount"
      :exclude-urls="items.map((item) => item?.url).filter(Boolean)"
      @close="assetPickerOpen = false"
      @confirm="addAssetItems"
      @notify="emit('notify', $event)"
    />
  </section>
</template>
