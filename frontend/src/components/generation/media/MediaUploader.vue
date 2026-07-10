<script setup>
import { computed } from "vue";
import { FileAudio, LoaderCircle, Trash2, Video } from "lucide-vue-next";
import { uploadAudio, uploadVideo } from "@/api/video.js";
import AssetPickerModal from "@/components/assets/AssetPickerModal.vue";
import ImageUploadSourcePanel from "@/components/generation/image/ImageUploadSourcePanel.vue";
import GeneratorPanelSection from "@/components/generation/workspace/GeneratorPanelSection.vue";
import { useMediaUploader } from "@/composables/generator/useMediaUploader.js";

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
  description: {
    type: String,
    default: "",
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

const icon = computed(() => (props.mediaType === "audio" ? FileAudio : Video));
const accept = computed(() => `${props.mediaType}/*`);
const canPickAsset = computed(() => props.showAssetButton);
const {
  addAssetItems,
  assetPickerOpen,
  clearItems,
  dragOver,
  fileInput,
  handleDrop,
  handleFileChange,
  openAssetPicker,
  remainingCount,
  removeItem,
  triggerFileInput,
} = useMediaUploader({
  props,
  emit,
  itemsKey: "items",
  updateEvent: "update:items",
  mediaType: props.mediaType,
  uploadFile: (file) => props.mediaType === "audio" ? uploadAudio(file) : uploadVideo(file),
  createPreview: (file) => URL.createObjectURL(file),
  mapAsset: (asset) => ({
    id: `asset_${asset.taskId || asset.id}`,
    previewUrl: asset.url,
    url: asset.url,
    objectKey: "",
    contentType: "",
    size: 0,
    name: asset.title || (props.mediaType === "audio" ? "资产库音频" : "资产库视频"),
    uploading: false,
    error: "",
    source: "asset",
    assetTaskId: asset.taskId || asset.id,
  }),
});
</script>

<template>
  <GeneratorPanelSection :title="title" :description="description" tone="muted">
    <template #meta>
      <span class="text-xs font-normal text-slate-400">(已选 {{ items.length }}/{{ maxCount }})</span>
    </template>
    <template #actions>
      <button
        v-if="items.length > 0"
        type="button"
        class="text-xs text-slate-400 transition-colors hover:text-rose-500"
        @click="clearItems"
      >
        清空
      </button>
    </template>

    <input ref="fileInput" type="file" :accept="accept" class="hidden" multiple @change="handleFileChange" />

    <div class="rounded-2xl border border-slate-200 bg-white p-3 shadow-sm">
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
            class="overflow-hidden rounded-xl border border-slate-100 bg-white"
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
    <slot name="after" />
  </GeneratorPanelSection>
</template>
