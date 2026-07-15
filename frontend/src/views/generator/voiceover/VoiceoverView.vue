<script setup>
import { onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import GenerationHistoryDrawer from "@/components/generation/workspace/GenerationHistoryDrawer.vue";
import GeneratorLayout from "@/components/layout/GeneratorLayout.vue";
import GenerationWorkspace from "@/components/generation/workspace/GenerationWorkspace.vue";
import VoiceoverSettingsPanel from "@/components/voiceover/VoiceoverSettingsPanel.vue";
import { useGeneratorRouteJob } from "@/composables/generator/restore/useGeneratorRouteJob.js";
import { useVoiceoverGenerator } from "@/composables/generator/useVoiceoverGenerator.js";
import { useConfirm } from "@/composables/useConfirm.js";
import { useToast } from "@/composables/useToast.js";

const route = useRoute();
const router = useRouter();
const confirm = useConfirm();
const toast = useToast();
const generator = useVoiceoverGenerator({ onJobCreated: (jobId) => router.replace(`/generator/voiceover/${jobId}`) });
const { openHistory, pickHistory, handleCreateNewTask, handleDeleteJob } = useGeneratorRouteJob({ generator, route, router, basePath: "/generator/voiceover", toast, confirm, deleteMessage: "确定删除这个AI配音任务吗？已生成音频仍保留在资产库。" });

onMounted(generator.loadConfig);
</script>

<template>
  <GeneratorLayout>
    <VoiceoverSettingsPanel :settings="generator.settings" :config="generator.config" :can-generate="generator.canGenerate.value" :creating="generator.creatingBatch.value" @update:settings="generator.updateSettings" @generate="generator.generate" @notify="generator.showNotice" />
    <GenerationWorkspace
      :settings="generator.settings" :current-task-title="generator.currentTaskTitle.value" :output-cards="generator.outputCards.value" :generating="generator.generating.value" :creating-batch="generator.creatingBatch.value" :generated-count="generator.generatedCount.value" :running-count="generator.runningCount.value" :failed-count="generator.failedCount.value" :total-count="generator.jobTotal.value" :job-total="generator.jobTotal.value" :gen-logs="generator.genLogs.value" :selected-cards-count="generator.selectedCardsCount.value" :downloading="generator.downloading.value" selected-image-label="MP3 / 24kHz" :get-module-name="generator.getModuleName" title-badge="本次AI配音" empty-title="AI 配音" empty-subtitle="选择音色并输入文本，生成可直接下载的 MP3 配音。" empty-image="https://image.nodepass.net/generated/2/2026/07/532e997786704728be5ac32a4a6f29eb.png" empty-image-alt="专业录音棚中的麦克风、耳机和音频波形" media-type="audio" media-unit="条" loading-title="AI 配音生成中" loading-description="正在创建语音合成任务" progress-text="正在生成配音"
      @update:current-task-title="generator.updateCurrentJobTitle" @select-all-cards="generator.toggleSelectAllCards" @batch-download="generator.batchDownload" @toggle-card="generator.toggleCardSelection" @download-card="generator.downloadSingleMedia" @delete-card="generator.removeCard" @create-new-task="handleCreateNewTask" @open-history="openHistory"
    />
    <GenerationHistoryDrawer :open="generator.showHistoryDrawer.value" :jobs="generator.historyTasks.value" :loading="generator.historyLoading.value" :current-job-id="generator.currentJobId.value" empty-hint="输入文本并选择音色后生成第一条配音" unit="条" @close="generator.showHistoryDrawer.value = false" @pick="pickHistory" @delete="handleDeleteJob" />
  </GeneratorLayout>
</template>
