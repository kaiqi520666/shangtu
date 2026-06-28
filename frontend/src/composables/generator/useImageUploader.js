import { computed, ref } from "vue";
import { uploadImage } from "@/api/image.js";

function readImagePreview(file) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = (event) => resolve(event.target.result);
    reader.readAsDataURL(file);
  });
}

function makeUploadPlaceholder(file, previewUrl, index) {
  return {
    id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}_${index}`,
    previewUrl,
    url: "",
    objectKey: "",
    contentType: file.type,
    size: file.size,
    uploading: true,
    error: "",
  };
}

function makeAssetImage(asset) {
  return {
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
  };
}

export function useImageUploader(props, emit) {
  const fileInput = ref(null);
  const dragOver = ref(false);
  const previewImage = ref(null);
  const assetPickerOpen = ref(false);

  const placeholderCount = computed(() => {
    if (!props.showPlaceholders) return 0;
    return Math.max(0, props.maxCount - props.images.length - 1);
  });
  const remainingCount = computed(() => Math.max(0, props.maxCount - props.images.length));
  const uploadActionText = computed(() => props.addText || "本地上传");
  const uploadHintDescription = computed(() => props.hintText || `最多 ${props.maxCount} 张`);

  function triggerFileInput() {
    fileInput.value?.click();
  }

  function openAssetPicker() {
    if (remainingCount.value <= 0) {
      emit("notify", props.limitMessage);
      return;
    }
    assetPickerOpen.value = true;
  }

  function patchImage(localId, patch) {
    const next = props.images.map((item) => (item && item.id === localId ? { ...item, ...patch } : item));
    emit("update:images", next);
  }

  async function uploadProcessedFile(file, localId) {
    try {
      const result = await uploadImage(file);
      if (result.code !== 0) {
        patchImage(localId, { uploading: false, error: result.message || "图片上传失败" });
        emit("notify", result.message || "图片上传失败");
        return;
      }
      patchImage(localId, {
        uploading: false,
        error: "",
        url: result.data.url,
        objectKey: result.data.object_key,
        contentType: result.data.content_type,
        size: result.data.size,
      });
    } catch (error) {
      const status = error.response?.status;
      emit("notify", status === 401 ? "登录已过期，请重新登录" : error.response?.data?.message || "图片上传失败");
      patchImage(localId, { uploading: false, error: "图片上传失败" });
    }
  }

  async function processFiles(files) {
    const imageFiles = files.filter((file) => file.type.startsWith("image/"));
    const limit = props.maxCount - props.images.length;
    if (limit <= 0) {
      emit("notify", props.limitMessage);
      return;
    }

    const toProcess = imageFiles.slice(0, limit);
    if (imageFiles.length > toProcess.length) {
      emit("notify", `已达到 ${props.maxCount} 张上限，多余图片未添加`);
    }
    if (toProcess.length === 0) return;

    // 先并行生成本地预览，立刻塞入占位项。
    const previews = await Promise.all(toProcess.map((file) => readImagePreview(file)));
    const placeholders = toProcess.map((file, index) => makeUploadPlaceholder(file, previews[index], index));
    emit("update:images", [...props.images, ...placeholders]);

    await Promise.all(
      toProcess.map((file, index) => uploadProcessedFile(file, placeholders[index].id)),
    );
  }

  function handleFileChange(event) {
    processFiles(Array.from(event.target.files || []));
    event.target.value = "";
  }

  function handleDrop(event) {
    dragOver.value = false;
    processFiles(Array.from(event.dataTransfer.files || []));
  }

  function removeImage(index) {
    const nextImages = props.images.filter((_, imageIndex) => imageIndex !== index);
    emit("update:images", nextImages);

    if (props.mainIndex >= nextImages.length) {
      emit("update:mainIndex", Math.max(0, nextImages.length - 1));
    } else if (index < props.mainIndex) {
      emit("update:mainIndex", props.mainIndex - 1);
    }
  }

  function clearImages() {
    emit("update:images", []);
    emit("update:mainIndex", 0);
    previewImage.value = null;
  }

  function addAssetImages(assets) {
    const limit = remainingCount.value;
    if (limit <= 0) {
      emit("notify", props.limitMessage);
      return;
    }

    const selected = assets.slice(0, limit);
    if (assets.length > selected.length) {
      emit("notify", `已达到 ${props.maxCount} 张上限，多余图片未添加`);
    }
    emit("update:images", [...props.images, ...selected.map(makeAssetImage)]);
    assetPickerOpen.value = false;
  }

  function getPreview(img) {
    if (!img) return "";
    if (typeof img === "string") return img;
    return img.previewUrl || img.url || "";
  }

  function openPreview(img) {
    if (!getPreview(img)) return;
    previewImage.value = img;
  }

  return {
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
  };
}
