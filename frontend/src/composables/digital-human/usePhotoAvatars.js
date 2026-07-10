import { computed, onBeforeUnmount, ref } from "vue";
import {
  deletePhotoAvatar,
  deletePhotoAvatarTask,
  getPhotoAvatarTasks,
  getPhotoAvatars,
  pollPhotoAvatarTask,
  uploadPhotoAvatar,
} from "@/api/digitalHuman.js";
import { useHeygenResourcePicker } from "@/composables/digital-human/useHeygenResourcePicker.js";
import { useConfirm } from "@/composables/useConfirm.js";

const POLL_INTERVAL_MS = 5000;

export function normalizeAvatar(item) {
  if (!item?.avatar_id) return null;
  return { ...item, source: item.source || "system", asset_id: item.asset_id || "", avatar_type: item.avatar_type || "studio_avatar" };
}

export function usePhotoAvatars({ selectedAvatar, notifyError }) {
  const confirm = useConfirm();
  const uploadDragOver = ref(false);
  const creating = ref(false);
  const deletingTaskId = ref("");
  const deletingAssetId = ref("");
  const name = ref("");
  const file = ref(null);
  const previewUrl = ref("");
  let pollTimer = null;

  const avatars = useHeygenResourcePicker({
    listApi: getPhotoAvatars,
    defaultFilters: {},
    buildParams: ({ page, pageSize }) => ({ page, page_size: pageSize }),
    pageSize: 12,
  });
  const tasks = useHeygenResourcePicker({
    listApi: getPhotoAvatarTasks,
    defaultFilters: {},
    buildParams: ({ page, pageSize }) => ({ page, page_size: pageSize }),
    pageSize: 12,
  });
  const taskItems = computed(() => tasks.state.items.filter((item) => item.status !== "done" || !item.result_avatar_id));

  function clearPreviewUrl() {
    if (!previewUrl.value) return;
    URL.revokeObjectURL(previewUrl.value);
    previewUrl.value = "";
  }

  function resetUpload() {
    name.value = "";
    file.value = null;
    uploadDragOver.value = false;
    clearPreviewUrl();
  }

  function stopPolling() {
    if (!pollTimer) return;
    window.clearInterval(pollTimer);
    pollTimer = null;
  }

  async function reload() {
    const [avatarResult, taskResult] = await Promise.all([avatars.reload(), tasks.reload()]);
    if (!avatarResult.ok) notifyError(avatarResult.message || "照片数字人加载失败");
    if (!taskResult.ok) notifyError(taskResult.message || "照片数字人任务加载失败");
  }

  async function pollRunningTasks() {
    const running = taskItems.value.filter((item) => ["pending", "processing"].includes(item.status));
    if (!running.length) return stopPolling();
    try {
      await Promise.all(running.map(async (item) => {
        const result = await pollPhotoAvatarTask(item.id);
        if (result.code !== 0) throw new Error(result.message || "照片数字人状态查询失败");
      }));
      await reload();
    } catch (error) {
      notifyError(error.message || "照片数字人状态查询失败");
      stopPolling();
    }
  }

  function startPolling() {
    stopPolling();
    if (!taskItems.value.length) return;
    pollTimer = window.setInterval(pollRunningTasks, POLL_INTERVAL_MS);
  }

  async function init() {
    avatars.reset();
    tasks.reset();
    await reload();
    startPolling();
  }

  async function reachEnd(event) {
    const [taskResult, avatarResult] = await Promise.all([tasks.handleScroll(event), avatars.handleScroll(event)]);
    if (!taskResult.ok) notifyError(taskResult.message || "照片数字人任务加载失败");
    if (!avatarResult.ok) notifyError(avatarResult.message || "照片数字人加载失败");
  }

  function setFile(nextFile) {
    if (!nextFile) return;
    if (!nextFile.type.startsWith("image/") && !/\.(jpg|jpeg|png|webp|gif)$/i.test(nextFile.name || "")) {
      notifyError("请选择图片文件");
      return;
    }
    file.value = nextFile;
    if (!name.value.trim()) name.value = (nextFile.name || "").replace(/\.[^/.]+$/, "").trim().slice(0, 120);
    clearPreviewUrl();
    previewUrl.value = URL.createObjectURL(nextFile);
  }

  function handleFileChange(event) {
    setFile(Array.from(event.target.files || [])[0]);
    event.target.value = "";
  }

  function handleDrop(event) {
    uploadDragOver.value = false;
    setFile(Array.from(event.dataTransfer.files || [])[0]);
  }

  async function create() {
    const avatarName = name.value.trim();
    if (!file.value) return notifyError("请先上传 1 张照片");
    if (!avatarName) return notifyError("请输入数字人名称");
    creating.value = true;
    try {
      const result = await uploadPhotoAvatar({ file: file.value, name: avatarName });
      if (result.code !== 0) return notifyError(result.message || "照片数字人创建失败");
      resetUpload();
      await reload();
      if (result.data?.status === "done" && result.data?.result_avatar_id) {
        const matched = avatars.state.items.find((item) => item.id === result.data.result_avatar_id);
        if (matched) selectedAvatar.value = normalizeAvatar(matched);
      }
      startPolling();
    } catch (error) {
      const detail = error.response?.data?.detail;
      const detailMessage = Array.isArray(detail) ? detail.map((item) => item?.msg).filter(Boolean).join("，") : "";
      notifyError(error.response?.data?.message || detailMessage || "照片数字人创建失败");
    } finally {
      creating.value = false;
    }
  }

  async function removeAvatar(item) {
    if (!item?.id) return;
    const approved = await confirm.open({ title: "删除照片数字人", message: "确定删除这个照片数字人吗？删除后不会影响历史任务快照。", confirmText: "删除", cancelText: "取消", tone: "danger" });
    if (!approved) return;
    deletingAssetId.value = item.id;
    try {
      const result = await deletePhotoAvatar(item.id);
      if (result.code !== 0) return notifyError(result.message || "删除失败");
      if (selectedAvatar.value?.source === "photo" && selectedAvatar.value?.asset_id === item.id) selectedAvatar.value = null;
      await reload();
    } catch (error) {
      notifyError(error.response?.data?.message || "删除失败，请稍后重试");
    } finally {
      deletingAssetId.value = "";
    }
  }

  async function removeTask(item) {
    if (!item?.id || item.status !== "failed") return;
    const approved = await confirm.open({ title: "删除失败任务", message: "确定删除这条失败任务吗？删除后将不再显示。", confirmText: "删除", cancelText: "取消", tone: "danger" });
    if (!approved) return;
    deletingTaskId.value = item.id;
    try {
      const result = await deletePhotoAvatarTask(item.id);
      if (result.code !== 0) return notifyError(result.message || "删除失败");
      await reload();
    } catch (error) {
      notifyError(error.response?.data?.message || "删除失败，请稍后重试");
    } finally {
      deletingTaskId.value = "";
    }
  }

  function select(item) {
    selectedAvatar.value = normalizeAvatar(item);
  }

  function isSelected(item) {
    const next = normalizeAvatar(item);
    if (!selectedAvatar.value || !next) return false;
    if (selectedAvatar.value.source === "photo" || next.source === "photo") {
      if (selectedAvatar.value.asset_id && next.asset_id) return selectedAvatar.value.asset_id === next.asset_id;
    }
    return selectedAvatar.value.avatar_id === next.avatar_id;
  }

  onBeforeUnmount(() => {
    stopPolling();
    clearPreviewUrl();
  });

  return { avatars, tasks, taskItems, uploadDragOver, creating, deletingTaskId, deletingAssetId, name, previewUrl, init, reachEnd, startPolling, stopPolling, resetUpload, handleFileChange, handleDrop, create, removeAvatar, removeTask, select, isSelected };
}
