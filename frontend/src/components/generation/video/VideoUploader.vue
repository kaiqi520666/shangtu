<script setup>
import { computed } from "vue";
import MediaUploader from "@/components/generation/media/MediaUploader.vue";

const props = defineProps({
  video: {
    type: Object,
    default: null,
  },
  title: {
    type: String,
    default: "参考视频",
  },
  addText: {
    type: String,
    default: "添加参考视频",
  },
  hintText: {
    type: String,
    default: "必须选择 1 条视频",
  },
});

const emit = defineEmits(["update:video", "notify"]);

const items = computed(() => (props.video ? [props.video] : []));

function updateItems(nextItems) {
  emit("update:video", nextItems[0] || null);
}
</script>

<template>
  <MediaUploader
    :items="items"
    media-type="video"
    :title="title"
    :add-text="addText"
    :hint-text="hintText"
    :max-count="1"
    limit-message="最多只能选择 1 条视频"
    @update:items="updateItems"
    @notify="emit('notify', $event)"
  />
</template>
