import { computed, nextTick, onBeforeUnmount, ref } from "vue";

function uploadId(index) {
  return `${Date.now()}_${Math.random().toString(36).slice(2, 8)}_${index}`;
}

export function useMediaUploader({
  props,
  emit,
  itemsKey,
  updateEvent,
  mediaType,
  uploadFile,
  createPreview,
  mapAsset,
  afterRemove,
  itemUnit = "个",
  uploadErrorMessage = "素材上传失败",
}) {
  const fileInput = ref(null);
  const dragOver = ref(false);
  const assetPickerOpen = ref(false);
  const items = computed(() => props[itemsKey]);
  const remainingCount = computed(() => Math.max(0, props.maxCount - items.value.length));

  function updateItems(nextItems) {
    emit(updateEvent, nextItems);
  }

  function notify(message) {
    emit("notify", message);
  }

  function triggerFileInput() {
    fileInput.value?.click();
  }

  function openAssetPicker() {
    if (props.showAssetButton === false) return;
    if (remainingCount.value <= 0) return notify(props.limitMessage);
    assetPickerOpen.value = true;
  }

  function patchItem(id, patch) {
    updateItems(items.value.map((item) => (item.id === id ? { ...item, ...patch } : item)));
  }

  async function processFiles(files) {
    const matched = files.filter((file) => file.type.startsWith(`${mediaType}/`));
    if (remainingCount.value <= 0) return notify(props.limitMessage);
    const selected = matched.slice(0, remainingCount.value);
    if (matched.length > selected.length) notify(`已达到 ${props.maxCount} ${itemUnit}上限，多余素材未添加`);
    if (selected.length === 0) return;

    const previews = await Promise.all(selected.map(createPreview));
    const placeholders = selected.map((file, index) => ({
      id: uploadId(index),
      previewUrl: previews[index],
      url: "",
      objectKey: "",
      contentType: file.type,
      size: file.size,
      name: file.name || "",
      uploading: true,
      error: "",
      source: "upload",
    }));
    updateItems([...items.value, ...placeholders]);
    await nextTick();

    await Promise.all(selected.map(async (file, index) => {
      const item = placeholders[index];
      try {
        const result = await uploadFile(file);
        if (result.code !== 0) {
          patchItem(item.id, { uploading: false, error: result.message || uploadErrorMessage });
          notify(result.message || uploadErrorMessage);
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
        patchItem(item.id, { uploading: false, error: uploadErrorMessage });
        notify(error.response?.data?.message || uploadErrorMessage);
      }
    }));
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
    const selected = assets.slice(0, remainingCount.value).map(mapAsset);
    updateItems([...items.value, ...selected]);
    assetPickerOpen.value = false;
  }

  function revoke(item) {
    if (item?.previewUrl?.startsWith("blob:")) URL.revokeObjectURL(item.previewUrl);
  }

  function removeItem(index) {
    revoke(items.value[index]);
    const nextItems = items.value.filter((_, itemIndex) => itemIndex !== index);
    updateItems(nextItems);
    afterRemove?.(nextItems, index);
  }

  function clearItems() {
    items.value.forEach(revoke);
    updateItems([]);
    afterRemove?.([], -1);
  }

  onBeforeUnmount(() => items.value.forEach(revoke));

  return {
    addAssetItems,
    assetPickerOpen,
    clearItems,
    dragOver,
    fileInput,
    handleDrop,
    handleFileChange,
    openAssetPicker,
    processFiles,
    remainingCount,
    removeItem,
    triggerFileInput,
  };
}
