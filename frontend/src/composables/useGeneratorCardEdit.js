import { ref } from "vue";
import { deleteImageTask, regenerateImageTask } from "@/api/image.js";
import { ensureEnoughImageCredits } from "@/composables/useImageCreditCosts.js";

export function useGeneratorCardEdit({
  generator,
  toast,
  confirm,
  afterRegenerateCardUpdate,
} = {}) {
  const editModalOpen = ref(false);
  const editCard = ref(null);
  const editSubmitting = ref(false);

  function openEditModal(card) {
    if (card.status !== "done" || !card.dataUrl) return;
    editCard.value = card;
    editModalOpen.value = true;
  }

  function closeEditModal() {
    editModalOpen.value = false;
    editCard.value = null;
    editSubmitting.value = false;
  }

  async function handleRegenerate(userPrompt) {
    const prompt = (userPrompt || "").trim();
    if (!prompt) {
      toast.info("请输入用户提示词");
      return;
    }

    const card = editCard.value;
    if (!card) return;
    if (!card.taskId) {
      toast.error("该图片缺少任务 ID，无法重新生成");
      return;
    }
    const hasEnoughCredits = await ensureEnoughImageCredits({
      quality: card.settingsSnapshot?.quality || "1K",
      count: 1,
      toast,
      actionText: "重新生成",
    });
    if (!hasEnoughCredits) return;

    editSubmitting.value = true;
    try {
      const res = await regenerateImageTask(card.taskId, "", prompt);
      if (!res || res.code !== 0) {
        toast.error((res && res.message) || "重新生成失败");
        editSubmitting.value = false;
        return;
      }

      const newTaskId = res.data?.task_id;
      if (!newTaskId) {
        toast.error("重新生成失败：缺少新任务 ID");
        editSubmitting.value = false;
        return;
      }

      const target = generator.outputCards.value.find((c) => c.taskId === card.taskId);
      if (target) {
        target.id = newTaskId;
        target.taskId = newTaskId;
        target.previousResultUrl = target.resultUrl || target.dataUrl || "";
        target.dataUrl = "";
        target.resultUrl = "";
        target.status = "processing";
        target.errorMessage = "";
        target.userPrompt = prompt;
        afterRegenerateCardUpdate?.(target, prompt);
      }

      closeEditModal();
      toast.success("已提交重新生成，请稍候...");
      if (target) {
        generator.startPollingCard(target);
      }
    } catch {
      toast.error("重新生成失败，请稍后重试");
      editSubmitting.value = false;
    }
  }

  async function deleteCard(card, { closeModal = false, message = "确定删除这张图片吗？" } = {}) {
    if (!card) return;

    const ok = await confirm.open({
      title: "删除图片",
      message,
      confirmText: "删除",
      cancelText: "取消",
      tone: "danger",
    });
    if (!ok) return;

    try {
      const res = await deleteImageTask(card.taskId);
      if (res.code !== 0) {
        toast.error(res.message || "删除失败");
        return;
      }

      const idx = generator.outputCards.value.findIndex((c) => c.id === card.id);
      if (idx > -1) generator.outputCards.value.splice(idx, 1);
      if (closeModal || editCard.value?.id === card.id) {
        closeEditModal();
      }
      toast.success("图片已删除");
    } catch {
      toast.error("删除失败，请稍后重试");
    }
  }

  function handleDeleteCard() {
    return deleteCard(editCard.value, {
      closeModal: true,
      message: "确定删除这张图片吗？图片不会立即从存储中物理删除。",
    });
  }

  function handleDeleteCardDirect(card) {
    return deleteCard(card);
  }

  return {
    editModalOpen,
    editCard,
    editSubmitting,
    openEditModal,
    closeEditModal,
    handleRegenerate,
    handleDeleteCard,
    handleDeleteCardDirect,
  };
}
