<script setup>
import { reactive, ref } from "vue";
import GenerationWorkspace from "@/components/generation/GenerationWorkspace.vue";
import GeneratorLayout from "@/components/layout/GeneratorLayout.vue";
import VideoSettingsPanel from "@/components/product-video/VideoSettingsPanel.vue";
import { defaultVideoCreditCosts, videoDemoTypes } from "@/constants/productVideo.js";
import { useToast } from "@/composables/useToast.js";

const toast = useToast();
const settings = reactive({
  videoType: videoDemoTypes[0].typeId,
  inputMode: videoDemoTypes[0].inputMode,
  market: "global",
  language: "english",
  sizePreset: "tiktok_9_16",
  duration: 6,
  resolution: "720p",
  productInput: "",
});
const uploadedImages = ref([]);
const mainImageIndex = ref(0);
const creditCosts = ref({ ...defaultVideoCreditCosts });
const currentTaskTitle = ref("");
const outputCards = ref([]);
const genLogs = ref([]);

function updateSettings(nextSettings) {
  Object.assign(settings, nextSettings);
}

function showNotice(message) {
  toast.info(message);
}

function handleGenerate() {
  toast.info("商品视频生成后端还未接入，当前先用于确认页面和交互感觉");
}

function getVideoModuleName(typeId) {
  return videoDemoTypes.find((item) => item.typeId === typeId)?.title || "商品视频";
}
</script>

<template>
  <GeneratorLayout>
    <VideoSettingsPanel
      :settings="settings"
      :uploaded-images="uploadedImages"
      :main-image-index="mainImageIndex"
      :credit-costs="creditCosts"
      @update:settings="updateSettings"
      @update:uploaded-images="uploadedImages = $event"
      @update:main-image-index="mainImageIndex = $event"
      @notify="showNotice"
      @generate="handleGenerate"
    />

    <GenerationWorkspace
      :settings="settings"
      :current-task-title="currentTaskTitle"
      :output-cards="outputCards"
      :generating="false"
      :creating-batch="false"
      :generated-count="0"
      :running-count="0"
      :failed-count="0"
      :total-count="0"
      :job-total="0"
      :gen-logs="genLogs"
      :selected-cards-count="0"
      selected-image-label="商品视频"
      :get-module-name="getVideoModuleName"
      title-badge="商品视频任务"
      empty-title="商品视频示例"
      empty-subtitle="这里仅用于预览不同电商视频风格，左侧选择的视频方向才会影响生成设置。"
      :empty-slides="videoDemoTypes"
      empty-media-type="video"
      loading-title="AI 商品视频生成中"
      progress-text="正在生成商品视频"
      poll-hint="每 5 秒轮询任务状态"
      @update:current-task-title="currentTaskTitle = $event"
      @create-new-task="showNotice('商品视频新建任务会在后端接入时开放')"
      @open-history="showNotice('商品视频生成记录会在后端接入时开放')"
    />
  </GeneratorLayout>
</template>
