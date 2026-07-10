import { ref } from "vue";
import { deleteDigitalHumanAudioAsset, getDigitalHumanAudioAssets, uploadDigitalHumanAudioAsset } from "@/api/digitalHuman.js";
import { useHeygenResourcePicker } from "@/composables/digital-human/useHeygenResourcePicker.js";

export function normalizeUploadAudio(item) {
  if (!item?.id && !item?.audio_asset_id) return null;
  return { ...item, mode: "upload", audio_asset_id: item.audio_asset_id || item.id };
}

export function useAudioAssets({ selectedVoice, notify }) {
  const uploadDragOver = ref(false);
  const uploading = ref(false);
  const deletingId = ref("");
  const picker = useHeygenResourcePicker({
    listApi: getDigitalHumanAudioAssets,
    defaultFilters: {},
    buildParams: ({ page, pageSize }) => ({ page, page_size: pageSize }),
    pageSize: 12,
  });

  async function init() {
    picker.reset();
    const result = await picker.reload();
    if (!result.ok) notify(result.message || "上传音频列表加载失败");
  }

  function readDuration(file) {
    return new Promise((resolve) => {
      const objectUrl = URL.createObjectURL(file);
      const audio = new Audio();
      const cleanup = (duration = 0) => {
        URL.revokeObjectURL(objectUrl);
        resolve(Math.max(0, Math.ceil(Number(duration || 0))));
      };
      audio.preload = "metadata";
      audio.onloadedmetadata = () => cleanup(audio.duration);
      audio.onerror = () => cleanup();
      audio.src = objectUrl;
    });
  }

  async function upload(file) {
    if (!file) return;
    if (!file.type.startsWith("audio/") && !/\.(mp3|wav|m4a|aac|ogg|webm|flac)$/i.test(file.name || "")) return notify("请选择音频文件");
    uploading.value = true;
    try {
      const durationSeconds = await readDuration(file);
      const result = await uploadDigitalHumanAudioAsset(file, { durationSeconds });
      if (result.code !== 0) return notify(result.message || "音频上传失败");
      selectedVoice.value = normalizeUploadAudio(result.data);
      await init();
    } catch (error) {
      notify(error.response?.data?.message || "音频上传失败");
    } finally {
      uploading.value = false;
    }
  }

  function handleFileChange(event) {
    upload(Array.from(event.target.files || [])[0]);
    event.target.value = "";
  }

  function handleDrop(event) {
    uploadDragOver.value = false;
    upload(Array.from(event.dataTransfer.files || [])[0]);
  }

  async function remove(item) {
    if (!item?.id || !window.confirm("确定删除这个音频吗？")) return;
    deletingId.value = item.id;
    try {
      const result = await deleteDigitalHumanAudioAsset(item.id);
      if (result.code !== 0) return notify(result.message || "删除失败");
      if (selectedVoice.value?.mode === "upload" && selectedVoice.value?.audio_asset_id === item.id) selectedVoice.value = null;
      await init();
    } catch (error) {
      notify(error.response?.data?.message || "删除失败，请稍后重试");
    } finally {
      deletingId.value = "";
    }
  }

  return { picker, uploadDragOver, uploading, deletingId, init, upload, handleFileChange, handleDrop, remove };
}
