<script setup>
const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
  index: {
    type: Number,
    required: true,
  },
  compact: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["update"]);

function updateField(key, value) {
  emit("update", props.index, {
    [key]: value,
  });
}
</script>

<template>
  <article
    class="border border-slate-200 bg-white shadow-sm transition-all hover:border-primary/30 hover:shadow-md"
    :class="compact ? 'rounded-xl p-3' : 'rounded-2xl p-4'"
  >
    <div class="mb-3">
      <h3 class="text-xs font-bold text-primary">{{ item.name }}</h3>
    </div>

    <textarea
      :value="item.content"
      :rows="compact ? 14 : 16"
      class="w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-700 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:bg-white focus:ring-1 focus:ring-primary"
      placeholder="编辑视频脚本策略"
      @input="updateField('content', $event.target.value)"
    ></textarea>
  </article>
</template>
