import { computed, ref } from "vue";
import { uploadImage } from "@/api/image.js";
import { useMediaUploader } from "@/composables/generator/useMediaUploader.js";

function readImagePreview(file) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (event) => resolve(event.target.result);
    reader.readAsDataURL(file);
  });
}

export function useImageUploader(props, emit) {
  const previewImage = ref(null);
  const uploader = useMediaUploader({
    props,
    emit,
    itemsKey: "images",
    updateEvent: "update:images",
    mediaType: "image",
    uploadFile: uploadImage,
    createPreview: readImagePreview,
    itemUnit: "张",
    uploadErrorMessage: "图片上传失败",
    mapAsset: (asset) => ({
      id: `asset_${asset.taskId || asset.id}`,
      previewUrl: asset.thumbUrl || asset.previewUrl || asset.url,
      url: asset.url,
      objectKey: "",
      contentType: "",
      size: 0,
      uploading: false,
      error: "",
      source: "asset",
      assetTaskId: asset.taskId || asset.id,
    }),
    afterRemove(nextImages, removedIndex) {
      if (nextImages.length === 0) {
        emit("update:mainIndex", 0);
        previewImage.value = null;
      } else if (props.mainIndex >= nextImages.length) {
        emit("update:mainIndex", nextImages.length - 1);
      } else if (removedIndex >= 0 && removedIndex < props.mainIndex) {
        emit("update:mainIndex", props.mainIndex - 1);
      }
    },
  });

  const placeholderCount = computed(() => props.showPlaceholders ? Math.max(0, props.maxCount - props.images.length - 1) : 0);
  const uploadActionText = computed(() => props.addText || "本地上传");
  const uploadHintDescription = computed(() => props.hintText || `最多 ${props.maxCount} 张`);

  function getPreview(image) {
    if (!image) return "";
    if (typeof image === "string") return image;
    return image.previewUrl || image.url || "";
  }

  function openPreview(image) {
    if (getPreview(image)) previewImage.value = image;
  }

  return {
    ...uploader,
    addAssetImages: uploader.addAssetItems,
    clearImages: uploader.clearItems,
    getPreview,
    openPreview,
    placeholderCount,
    previewImage,
    removeImage: uploader.removeItem,
    uploadActionText,
    uploadHintDescription,
  };
}
