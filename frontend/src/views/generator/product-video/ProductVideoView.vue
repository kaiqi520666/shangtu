<script setup>
import { reactive, ref } from "vue";
import GeneratorLayout from "@/components/layout/GeneratorLayout.vue";
import VideoGenerationWorkspace from "@/components/product-video/VideoGenerationWorkspace.vue";
import VideoSettingsPanel from "@/components/product-video/VideoSettingsPanel.vue";
import { defaultVideoCreditCosts, getVideoDemoType, videoDemoTypes } from "@/constants/productVideo.js";
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

function updateSettings(nextSettings) {
  Object.assign(settings, nextSettings);
}

function selectVideoType(typeId) {
  const nextType = getVideoDemoType(typeId);
  Object.assign(settings, {
    videoType: typeId,
    inputMode: nextType.inputMode,
  });
  uploadedImages.value = [];
  mainImageIndex.value = 0;
}

function showNotice(message) {
  toast.info(message);
}

function handleGenerate() {
  toast.info("商品视频生成后端还未接入，当前先用于确认页面和交互感觉");
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

    <VideoGenerationWorkspace
      :settings="settings"
      :credit-costs="creditCosts"
      @select-type="selectVideoType"
      @notify="showNotice"
    />
  </GeneratorLayout>
</template>
