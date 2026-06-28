<script setup>
import { X } from "lucide-vue-next";
import AssetPickerModal from "@/components/assets/AssetPickerModal.vue";
import ImageUploadAddTile from "@/components/generation/image/ImageUploadAddTile.vue";
import ImageUploadItem from "@/components/generation/image/ImageUploadItem.vue";
import ImageUploadSourcePanel from "@/components/generation/image/ImageUploadSourcePanel.vue";
import AppModal from "@/components/ui/AppModal.vue";
import { useImageUploader } from "@/composables/generator/useImageUploader.js";

const props = defineProps({
  images: {
    type: Array,
    required: true,
  },
  mainIndex: {
    type: Number,
    default: 0,
  },
  title: {
    type: String,
    default: "商品详情图",
  },
  maxCount: {
    type: Number,
    default: 3,
  },
  addText: {
    type: String,
    default: "添加图片",
  },
  hintText: {
    type: String,
    default: "拖拽或点击",
  },
  altText: {
    type: String,
    default: "商品",
  },
  mainBadgeText: {
    type: String,
    default: "主",
  },
  limitMessage: {
    type: String,
    default: "最多只能上传 3 张商品图",
  },
  showPlaceholders: {
    type: Boolean,
    default: true,
  },
  showMainAction: {
    type: Boolean,
    default: true,
  },
  badgeTextResolver: {
    type: Function,
    default: null,
  },
});

const emit = defineEmits(["update:images", "update:mainIndex", "notify"]);

const {
  addAssetImages,
  assetPickerOpen,
  clearImages,
  dragOver,
  fileInput,
  getPreview,
  handleDrop,
  handleFileChange,
  openAssetPicker,
  openPreview,
  placeholderCount,
  previewImage,
  remainingCount,
  removeImage,
  triggerFileInput,
  uploadActionText,
  uploadHintDescription,
} = useImageUploader(props, emit);

function getBadgeText(index) {
  return props.badgeTextResolver ? props.badgeTextResolver(index) : props.mainBadgeText;
}

function shouldShowBadge(index) {
  if (props.badgeTextResolver) return true;
  return props.showMainAction && index === props.mainIndex;
}
</script>

<template>
  <section class="border-b border-slate-100 bg-slate-50/40 p-5">
    <div class="mb-3 flex items-center justify-between">
      <label class="flex items-center gap-1.5 text-xs font-bold text-slate-700">
        <span class="h-1.5 w-1.5 rounded-full bg-primary"></span>
        {{ title }}
        <span class="font-normal text-slate-400"
          >(支持最多 {{ maxCount }} 张，已选 {{ images.length }}/{{ maxCount }})</span
        >
      </label>
      <div class="flex shrink-0 items-center gap-2">
        <button
          v-if="images.length > 0"
          type="button"
          class="text-xs text-slate-400 transition-colors hover:text-rose-500"
          @click="clearImages"
        >
          清空
        </button>
      </div>
    </div>

    <input
      ref="fileInput"
      type="file"
      accept="image/*"
      class="hidden"
      multiple
      @change="handleFileChange"
    />

    <ImageUploadSourcePanel
      v-if="images.length === 0"
      :action-text="uploadActionText"
      :hint-text="uploadHintDescription"
      :drag-over="dragOver"
      @upload="triggerFileInput"
      @asset="openAssetPicker"
      @drag-over="dragOver = true"
      @drag-leave="dragOver = false"
      @drop="handleDrop"
    />

    <div v-else class="grid grid-cols-3 gap-3">
      <ImageUploadItem
        v-for="(img, index) in images"
        :key="img?.id || `${getPreview(img)}-${index}`"
        :image="img"
        :preview-url="getPreview(img)"
        :index="index"
        :alt-text="altText"
        :show-main-action="showMainAction"
        :is-main="index === mainIndex"
        :show-badge="shouldShowBadge(index)"
        :badge-text="getBadgeText(index)"
        @preview="openPreview(img)"
        @set-main="emit('update:mainIndex', index)"
        @remove="removeImage(index)"
      />

      <ImageUploadAddTile
        v-if="images.length < maxCount"
        :action-text="uploadActionText"
        :hint-text="uploadHintDescription"
        :drag-over="dragOver"
        @upload="triggerFileInput"
        @asset="openAssetPicker"
        @drag-over="dragOver = true"
        @drag-leave="dragOver = false"
        @drop="handleDrop"
      />

      <div
        v-for="slotIndex in placeholderCount"
        :key="slotIndex"
        class="hidden aspect-square rounded-xl border border-slate-100 bg-slate-50/40 sm:block"
      >
        <X class="m-auto mt-[40%] h-4 w-4 text-slate-200" />
      </div>
    </div>

    <AppModal
      :open="Boolean(previewImage)"
      :title="title"
      panel-class="w-full max-w-4xl"
      @close="previewImage = null"
    >
      <div v-if="previewImage" class="bg-slate-100 p-6">
        <img
          :src="getPreview(previewImage)"
          class="mx-auto max-h-[75vh] rounded-xl object-contain shadow-lg"
          :alt="altText"
        />
      </div>
    </AppModal>

    <AssetPickerModal
      :open="assetPickerOpen"
      media-type="image"
      title="从资产库选择图片"
      :max-count="remainingCount"
      :exclude-urls="images.map((img) => img?.url).filter(Boolean)"
      @close="assetPickerOpen = false"
      @confirm="addAssetImages"
      @notify="emit('notify', $event)"
    />
  </section>
</template>
