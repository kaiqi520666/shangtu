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

    <div class="grid gap-2" :class="compact ? 'grid-cols-1' : 'grid-cols-2'">
      <textarea
        :value="item.opening"
        rows="3"
        class="resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-700 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:bg-white focus:ring-1 focus:ring-primary"
        placeholder="开场"
        @input="updateField('opening', $event.target.value)"
      ></textarea>
      <textarea
        :value="item.motion"
        rows="3"
        class="resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-700 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:bg-white focus:ring-1 focus:ring-primary"
        placeholder="镜头运动"
        @input="updateField('motion', $event.target.value)"
      ></textarea>
      <textarea
        :value="item.sellingPoints"
        rows="3"
        class="resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-700 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:bg-white focus:ring-1 focus:ring-primary"
        placeholder="卖点呈现"
        @input="updateField('sellingPoints', $event.target.value)"
      ></textarea>
      <textarea
        :value="item.visualStyle"
        rows="3"
        class="resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-700 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:bg-white focus:ring-1 focus:ring-primary"
        placeholder="画面风格"
        @input="updateField('visualStyle', $event.target.value)"
      ></textarea>
    </div>

    <textarea
      :value="item.avoid"
      rows="3"
      class="mt-2 w-full resize-none rounded-xl border border-amber-200 bg-amber-50/60 p-3 text-xs leading-relaxed text-amber-900 outline-none transition-colors placeholder:text-amber-400 focus:border-amber-400 focus:bg-white focus:ring-1 focus:ring-amber-300"
      placeholder="避免事项"
      @input="updateField('avoid', $event.target.value)"
    ></textarea>

    <textarea
      :value="item.content"
      :rows="compact ? 7 : 8"
      class="mt-2 w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-700 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:bg-white focus:ring-1 focus:ring-primary"
      placeholder="完整视频脚本"
      @input="updateField('content', $event.target.value)"
    ></textarea>
  </article>
</template>
