<script setup>
import { GripVertical, Trash2 } from "lucide-vue-next";

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

const emit = defineEmits(["update", "remove"]);

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
    <div class="mb-3 flex select-none items-start justify-between" :class="compact ? 'gap-2' : 'gap-3'">
      <div class="flex min-w-0 items-start gap-3">
        <div
          class="drag-handle flex shrink-0 cursor-grab items-center justify-center rounded-xl border border-primary/20 bg-primary/10 text-primary transition-colors hover:border-primary/30 hover:bg-primary/15 active:cursor-grabbing"
          :class="compact ? 'h-8 w-8' : 'h-9 w-9'"
          title="拖动排序"
        >
          <GripVertical class="pointer-events-none h-4 w-4" />
        </div>
        <div class="min-w-0">
          <h3 class="text-xs font-bold text-primary">{{ item.name }}</h3>
          <p class="mt-1 text-xs leading-relaxed text-slate-500" :class="compact ? 'line-clamp-2' : ''">
            {{ item.strategy }}
          </p>
        </div>
      </div>

      <button
        type="button"
        class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-400 transition-colors hover:border-red-200 hover:bg-red-50 hover:text-red-500"
        title="删除"
        @click="emit('remove', index)"
      >
        <Trash2 class="h-3.5 w-3.5" />
      </button>
    </div>

    <div class="grid gap-2" :class="compact ? 'grid-cols-1' : 'grid-cols-2'">
      <textarea
        :value="item.pose"
        rows="3"
        class="resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-700 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:bg-white focus:ring-1 focus:ring-primary"
        placeholder="模特姿态"
        @input="updateField('pose', $event.target.value)"
      ></textarea>
      <textarea
        :value="item.camera"
        rows="3"
        class="resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-700 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:bg-white focus:ring-1 focus:ring-primary"
        placeholder="镜头角度"
        @input="updateField('camera', $event.target.value)"
      ></textarea>
    </div>

    <textarea
      :value="item.fidelity"
      rows="3"
      class="mt-2 w-full resize-none rounded-xl border border-amber-200 bg-amber-50/60 p-3 text-xs leading-relaxed text-amber-900 outline-none transition-colors placeholder:text-amber-400 focus:border-amber-400 focus:bg-white focus:ring-1 focus:ring-amber-300"
      placeholder="服装保真约束：颜色、版型、材质、图案、长度、领口、袖型、廓形等必须保持一致"
      @input="updateField('fidelity', $event.target.value)"
    ></textarea>

    <textarea
      :value="item.content"
      :rows="compact ? 5 : 6"
      class="mt-2 w-full resize-none rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs leading-relaxed text-slate-700 outline-none transition-colors placeholder:text-slate-400 focus:border-primary focus:bg-white focus:ring-1 focus:ring-primary"
      placeholder="完整穿搭策略，可补充场景氛围、动作节奏和画面注意事项"
      @input="updateField('content', $event.target.value)"
    ></textarea>
  </article>
</template>
