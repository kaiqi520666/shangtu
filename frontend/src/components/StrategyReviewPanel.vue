<script setup>
import { computed, ref, watch } from "vue";
import { ArrowLeft, CheckCircle2, LoaderCircle, Sparkles, WandSparkles } from "lucide-vue-next";
import draggable from "vuedraggable";
import StrategyModuleCard from "@/components/StrategyModuleCard.vue";

const props = defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  brief: {
    type: String,
    default: "",
  },
  modules: {
    type: Array,
    required: true,
  },
  settings: {
    type: Object,
    required: true,
  },
  selectedImageLabel: {
    type: String,
    required: true,
  },
  placement: {
    type: String,
    default: "workspace",
  },
});

const emit = defineEmits(["back", "confirm", "update-module", "reorder-modules", "remove-module"]);

const isSide = computed(() => props.placement === "side");
const localModules = ref([]);
const dragging = ref(false);

watch(
  () => props.modules,
  (modules) => {
    localModules.value = [...modules];
  },
  { immediate: true },
);

function handleDragChange() {
  emit("reorder-modules", [...localModules.value]);
}

function handleDragStart() {
  dragging.value = true;
}

function handleDragEnd() {
  dragging.value = false;
  emit("reorder-modules", [...localModules.value]);
}

function handleModuleUpdate(localIndex, patch) {
  const moduleId = localModules.value[localIndex]?.id;
  const sourceIndex = props.modules.findIndex((module) => module.id === moduleId);
  if (sourceIndex === -1) return;
  emit("update-module", sourceIndex, patch);
}

function handleModuleRemove(localIndex) {
  const moduleId = localModules.value[localIndex]?.id;
  const sourceIndex = props.modules.findIndex((module) => module.id === moduleId);
  if (sourceIndex === -1) return;
  emit("remove-module", sourceIndex);
}
</script>

<template>
  <section
    class="flex h-full flex-col overflow-hidden bg-slate-50"
    :class="[
      isSide ? 'w-[420px] shrink-0 border-r border-slate-200' : 'flex-1',
      dragging ? 'select-none' : '',
    ]"
  >
    <div
      v-if="!isSide"
      class="z-10 flex h-14 shrink-0 items-center justify-between border-b border-slate-200 bg-white/90 px-6 shadow-sm backdrop-blur-sm"
    >
      <div class="flex min-w-0 items-center gap-3">
        <button
          type="button"
          class="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-500 transition-colors hover:border-primary/30 hover:bg-primary/5 hover:text-primary"
          @click="emit('back')"
        >
          <ArrowLeft class="h-4 w-4" />
        </button>
        <div class="min-w-0">
          <h2 class="text-sm font-bold text-slate-900">模块策略与设计规范</h2>
          <p class="truncate text-xs text-slate-500">
            {{ settings.platform }} / {{ settings.language }} / {{ selectedImageLabel }}
          </p>
        </div>
      </div>

      <button
        v-if="!loading && !isSide"
        type="button"
        class="flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-xs font-bold text-white shadow-md shadow-primary/20 transition-all hover:-translate-y-0.5 hover:bg-secondary"
        @click="emit('confirm')"
      >
        <WandSparkles class="h-4 w-4" />
        生成详情图（{{ modules.length }}张）
      </button>
    </div>

    <div class="flex-1 overflow-y-auto" :class="isSide ? 'p-4' : 'p-6'">
      <div v-if="loading" class="flex min-h-full items-center justify-center">
        <div
          class="w-full rounded-3xl border border-primary/20 bg-white text-center shadow-xl shadow-primary/10"
          :class="isSide ? 'p-5' : 'max-w-xl p-8'"
        >
          <div
            class="relative mx-auto mb-6 flex items-center justify-center"
            :class="isSide ? 'h-20 w-20' : 'h-24 w-24'"
          >
            <div class="absolute inset-0 animate-ping rounded-full bg-primary/10"></div>
            <div
              class="absolute inset-3 animate-spin rounded-full border border-dashed border-primary/50"
            ></div>
            <Sparkles class="h-10 w-10 text-primary" />
          </div>
          <h3 class="text-lg font-bold text-slate-900">生成中...</h3>
          <p class="mx-auto mt-2 max-w-sm text-xs leading-relaxed text-slate-500">
            正在根据已选图种、平台规则和商品卖点，生成可编辑的模块内容与设计规范。
          </p>
          <div class="mt-6 overflow-hidden rounded-full border border-slate-200 bg-slate-100">
            <div
              class="h-2 w-2/3 animate-pulse rounded-full bg-gradient-to-r from-primary to-secondary"
            ></div>
          </div>
        </div>
      </div>

      <div v-else class="mx-auto flex flex-col" :class="isSide ? 'gap-3' : 'max-w-5xl gap-5'">
        <div
          class="rounded-2xl border border-primary/20 bg-white shadow-sm"
          :class="isSide ? 'p-4' : 'p-5'"
        >
          <div class="flex items-start gap-3">
            <div
              class="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary"
            >
              <CheckCircle2 class="h-5 w-5" />
            </div>
            <div class="min-w-0">
              <div class="flex flex-wrap items-center gap-2">
                <h3 class="text-sm font-bold text-slate-900">策略已生成</h3>
                <span class="rounded-full bg-primary/10 px-2 py-0.5 text-xs font-bold text-primary"
                  >{{ modules.length }} 个模块</span
                >
              </div>
              <p class="mt-1 text-xs leading-relaxed text-slate-500">{{ brief }}</p>
            </div>
          </div>
        </div>

        <draggable
          :list="localModules"
          tag="div"
          item-key="id"
          handle=".drag-handle"
          draggable=".strategy-module-item"
          direction="vertical"
          :animation="180"
          :force-fallback="true"
          :fallback-on-body="true"
          :fallback-tolerance="3"
          chosen-class="is-chosen"
          ghost-class="is-ghost"
          drag-class="is-dragging"
          :class="isSide ? 'flex flex-col gap-3' : 'grid gap-4 xl:grid-cols-2'"
          @start="handleDragStart"
          @end="handleDragEnd"
          @change="handleDragChange"
        >
          <template #item="{ element, index }">
            <div class="strategy-module-item">
              <StrategyModuleCard
                :module="element"
                :index="index"
                :compact="isSide"
                @update="handleModuleUpdate"
                @remove="handleModuleRemove"
              />
            </div>
          </template>
        </draggable>
      </div>
    </div>

    <div
      v-if="!loading"
      class="shrink-0 border-t border-slate-200 bg-white/95 backdrop-blur-sm"
      :class="isSide ? 'p-4' : 'px-6 py-4'"
    >
      <div
        class="mx-auto flex items-center justify-between gap-3"
        :class="isSide ? '' : 'max-w-5xl'"
      >
        <button
          type="button"
          class="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-bold text-slate-600 shadow-sm transition-colors hover:border-primary/30 hover:bg-primary/5 hover:text-primary"
          @click="emit('back')"
        >
          上一步
        </button>
        <button
          type="button"
          class="flex items-center justify-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-xs font-bold text-white shadow-md shadow-primary/20 transition-all hover:-translate-y-0.5 hover:bg-secondary"
          :class="isSide ? 'flex-1' : ''"
          @click="emit('confirm')"
        >
          <LoaderCircle class="h-4 w-4" />
          生成详情图（{{ modules.length }}张）
        </button>
      </div>
    </div>
  </section>
</template>
