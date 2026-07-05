<script setup>
import { onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import AvatarPickerModal from "@/components/digital-human/AvatarPickerModal.vue";
import DigitalHumanSettingsPanel from "@/components/digital-human/DigitalHumanSettingsPanel.vue";
import VoicePickerModal from "@/components/digital-human/VoicePickerModal.vue";
import GenerationHistoryDrawer from "@/components/generation/workspace/GenerationHistoryDrawer.vue";
import GenerationPreviewModal from "@/components/generation/workspace/GenerationPreviewModal.vue";
import GenerationWorkspace from "@/components/generation/workspace/GenerationWorkspace.vue";
import GeneratorLayout from "@/components/layout/GeneratorLayout.vue";
import { useDigitalHumanGenerator } from "@/composables/generator/useDigitalHumanGenerator.js";
import { useGeneratorRouteJob } from "@/composables/generator/restore/useGeneratorRouteJob.js";
import { useConfirm } from "@/composables/useConfirm.js";
import { useToast } from "@/composables/useToast.js";

const route = useRoute();
const router = useRouter();
const confirm = useConfirm();
const toast = useToast();
const digitalHuman = useDigitalHumanGenerator({
  toast,
  confirm,
  onJobCreated(jobId) {
    router.replace(`/generator/digital-human/${jobId}`);
  },
});
const zoomCard = ref(null);
const avatarPickerOpen = ref(false);
const voicePickerOpen = ref(false);

function openAvatarPicker() {
  avatarPickerOpen.value = true;
}

function openVoicePicker() {
  voicePickerOpen.value = true;
}

function handleAvatarConfirm(item) {
  digitalHuman.selectedAvatar.value = item;
}

function handleVoiceConfirm(item) {
  digitalHuman.selectedVoice.value = item;
}

const { openHistory, pickHistory, handleCreateNewTask, handleDeleteJob } = useGeneratorRouteJob({
  generator: digitalHuman,
  route,
  router,
  basePath: "/generator/digital-human",
  toast,
  confirm,
  deleteMessage: "确定删除这个生成任务吗？已生成视频不会立即从存储中物理删除。",
});

function openPreview(card) {
  if (card.status !== "done" || !card.dataUrl) return;
  zoomCard.value = card;
}

function closePreview() {
  zoomCard.value = null;
}

function closeHistoryDrawer() {
  digitalHuman.showHistoryDrawer.value = false;
}

onMounted(() => {
  digitalHuman.loadPricing();
});
</script>

<template>
  <GeneratorLayout>
    <DigitalHumanSettingsPanel
      :settings="digitalHuman.settings"
      :quality-options="digitalHuman.qualityOptions.value"
      :selected-avatar="digitalHuman.selectedAvatar.value"
      :selected-voice="digitalHuman.selectedVoice.value"
      :generate-disabled="!digitalHuman.canGenerate.value"
      :generate-text="digitalHuman.generateButtonText.value"
      :script-meta-text="digitalHuman.scriptMetaText.value"
      :script-exceeded="digitalHuman.scriptExceeded.value"
      @update:settings="digitalHuman.updateSettings"
      @open-avatar-picker="openAvatarPicker"
      @open-voice-picker="openVoicePicker"
      @generate="digitalHuman.generateDigitalHuman"
      @notify="digitalHuman.showNotice"
    />

    <GenerationWorkspace
      :settings="digitalHuman.settings"
      :current-task-title="digitalHuman.currentTaskTitle.value"
      :output-cards="digitalHuman.outputCards.value"
      :generating="digitalHuman.generating.value"
      :creating-batch="digitalHuman.creatingBatch.value"
      :generated-count="digitalHuman.generatedCount.value"
      :running-count="digitalHuman.runningCount.value"
      :failed-count="digitalHuman.failedCount.value"
      :total-count="digitalHuman.jobTotal.value"
      :job-total="digitalHuman.jobTotal.value"
      :gen-logs="digitalHuman.genLogs.value"
      :selected-cards-count="digitalHuman.selectedCardsCount.value"
      :downloading="digitalHuman.downloading.value"
      selected-image-label="数字人口播"
      :get-module-name="digitalHuman.getDigitalHumanModuleName"
      empty-title="数字人工作台"
      empty-subtitle="选择数字人、声音和口播文案后，这里会显示生成进度和成片结果。"
      :empty-slides="[]"
      media-type="video"
      media-unit="个"
      loading-title="数字人视频生成中"
      loading-description="正在提交 HeyGen 任务，稍后会在这里显示状态和成片结果。"
      progress-text="正在生成数字人视频"
      poll-hint="每 3 秒轮询任务状态"
      :language="digitalHuman.voiceLanguage.value"
      platform=""
      @update:current-task-title="digitalHuman.updateCurrentJobTitle"
      @select-all-cards="digitalHuman.toggleSelectAllCards"
      @batch-download="digitalHuman.batchDownload"
      @toggle-card="digitalHuman.toggleCardSelection"
      @download-card="digitalHuman.downloadSingleVideo"
      @zoom-card="openPreview"
      @delete-card="digitalHuman.removeCard"
      @create-new-task="handleCreateNewTask"
      @open-history="openHistory"
    />

    <GenerationHistoryDrawer
      :open="digitalHuman.showHistoryDrawer.value"
      :jobs="digitalHuman.historyTasks.value"
      :loading="digitalHuman.historyLoading.value"
      :current-job-id="digitalHuman.currentJobId.value"
      empty-hint="点击「新建任务」开始生成数字人视频"
      unit="个"
      @close="closeHistoryDrawer"
      @pick="pickHistory"
      @delete="handleDeleteJob"
    />

    <GenerationPreviewModal
      :card="zoomCard"
      title="数字人视频预览"
      alt="数字人视频预览"
      media-type="video"
      @close="closePreview"
    />

    <AvatarPickerModal
      :open="avatarPickerOpen"
      :selected-avatar="digitalHuman.selectedAvatar.value"
      @close="avatarPickerOpen = false"
      @confirm="handleAvatarConfirm"
      @notify="digitalHuman.showNotice"
    />

    <VoicePickerModal
      :open="voicePickerOpen"
      :selected-voice="digitalHuman.selectedVoice.value"
      @close="voicePickerOpen = false"
      @confirm="handleVoiceConfirm"
      @notify="digitalHuman.showNotice"
    />
  </GeneratorLayout>
</template>
