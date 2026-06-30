<script setup>
import { computed, ref, watch } from "vue";
import { Check, ChevronLeft, ChevronRight, ImageOff, LoaderCircle } from "lucide-vue-next";
import { listAssets } from "@/api/assets.js";
import AppModal from "@/components/ui/AppModal.vue";

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  mediaType: {
    type: String,
    default: "image",
  },
  maxCount: {
    type: Number,
    default: 1,
  },
  title: {
    type: String,
    default: "选择资产",
  },
  excludeUrls: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["close", "confirm", "notify"]);

const assets = ref([]);
const loading = ref(false);
const page = ref(1);
const pageSize = ref(18);
const total = ref(0);
const selectedMap = ref({});
const scenario = ref("");

const scenarioOptions = [
  { value: "", label: "全部" },
  { value: "product_suite", label: "商品套图" },
  { value: "product_image", label: "商品详情图" },
  { value: "outfit", label: "服饰穿搭" },
  { value: "free_image", label: "自由生图" },
  { value: "product_video", label: "商品视频" },
  { value: "free_video", label: "自由生视频" },
];

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)));
const selectedAssets = computed(() => Object.values(selectedMap.value));
const selectedCount = computed(() => selectedAssets.value.length);
const mediaLabel = computed(() => (props.mediaType === "video" ? "视频" : "图片"));

watch(
  () => props.open,
  (open) => {
    if (!open) return;
    page.value = 1;
    selectedMap.value = {};
    loadAssets();
  },
);

async function loadAssets() {
  loading.value = true;
  try {
    const result = await listAssets({
      scenario: scenario.value,
      media_type: props.mediaType,
      page: page.value,
      page_size: pageSize.value,
    });
    if (result.code !== 0) {
      emit("notify", result.message || "资产加载失败");
      assets.value = [];
      total.value = 0;
      return;
    }
    const data = result.data || {};
    total.value = data.total || 0;
    assets.value = (data.items || []).map((item) => ({
      id: item.task_id,
      taskId: item.task_id,
      url: item.result_url || "",
      resultUrl: item.result_url || "",
      thumbUrl: item.thumb_url || item.result_url || "",
      previewUrl: item.preview_url || item.result_url || "",
      title: item.title || item.job_title || mediaLabel.value,
      typeId: item.type_id || "",
      scenario: item.scenario || "",
      mediaType: item.media_type || props.mediaType,
      createdAt: item.created_at || "",
    }));
  } catch (error) {
    emit("notify", error.response?.data?.message || "资产加载失败");
    assets.value = [];
    total.value = 0;
  } finally {
    loading.value = false;
  }
}

function changeScenario(value) {
  scenario.value = value;
  page.value = 1;
  loadAssets();
}

function changePage(nextPage) {
  if (nextPage < 1 || nextPage > totalPages.value) return;
  page.value = nextPage;
  loadAssets();
}

function isExcluded(asset) {
  return props.excludeUrls.includes(asset.url);
}

function isSelected(asset) {
  return Boolean(selectedMap.value[asset.id]);
}

function toggleAsset(asset) {
  if (!asset.url || isExcluded(asset)) return;
  const next = { ...selectedMap.value };
  if (next[asset.id]) {
    delete next[asset.id];
    selectedMap.value = next;
    return;
  }
  if (selectedCount.value >= props.maxCount) {
    emit("notify", `最多选择 ${props.maxCount} 个${mediaLabel.value}资产`);
    return;
  }
  next[asset.id] = asset;
  selectedMap.value = next;
}

function confirmSelection() {
  if (selectedCount.value === 0) {
    emit("notify", `请选择${mediaLabel.value}资产`);
    return;
  }
  emit("confirm", selectedAssets.value);
}
</script>

<template>
  <AppModal
    :open="open"
    :title="title"
    :subtitle="`最多选择 ${maxCount} 个${mediaLabel}资产`"
    panel-class="w-full max-w-5xl"
    @close="emit('close')"
  >
    <div class="flex min-h-[620px] flex-col overflow-hidden">
      <div class="flex shrink-0 items-center justify-between gap-3 border-b border-slate-100 px-5 py-3">
        <div class="flex flex-wrap gap-2">
          <button
            v-for="option in scenarioOptions"
            :key="option.value"
            type="button"
            class="rounded-full border px-3 py-1 text-xs font-bold transition-colors"
            :class="
              scenario === option.value
                ? 'border-primary bg-primary/10 text-primary'
                : 'border-slate-200 bg-white text-slate-500 hover:border-slate-300 hover:bg-slate-50'
            "
            @click="changeScenario(option.value)"
          >
            {{ option.label }}
          </button>
        </div>
        <span class="shrink-0 text-xs font-semibold text-slate-400">
          已选 {{ selectedCount }}/{{ maxCount }}
        </span>
      </div>

      <div class="min-h-0 flex-1 overflow-y-auto bg-slate-50/70 p-5">
        <div v-if="loading" class="flex h-80 items-center justify-center text-sm font-semibold text-slate-400">
          <LoaderCircle class="mr-2 h-5 w-5 animate-spin" />
          加载资产中...
        </div>
        <div v-else-if="assets.length === 0" class="flex h-80 flex-col items-center justify-center text-slate-400">
          <ImageOff class="h-10 w-10" />
          <p class="mt-3 text-sm font-semibold">暂无可选{{ mediaLabel }}资产</p>
        </div>
        <div v-else class="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4">
          <button
            v-for="asset in assets"
            :key="asset.id"
            type="button"
            class="group relative overflow-hidden rounded-xl border bg-white text-left shadow-sm transition-all"
            :class="
              isSelected(asset)
                ? 'border-primary ring-2 ring-primary/15'
                : isExcluded(asset)
                  ? 'cursor-not-allowed border-slate-100 opacity-50'
                  : 'border-slate-200 hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-md'
            "
            @click="toggleAsset(asset)"
          >
            <div class="relative flex aspect-square items-center justify-center bg-slate-100 p-2">
              <video
                v-if="asset.mediaType === 'video'"
                :src="asset.url"
                class="h-full w-full rounded-lg object-cover"
                muted
                playsinline
                preload="metadata"
              ></video>
              <img
                v-else
                :src="asset.thumbUrl || asset.url"
                class="max-h-full max-w-full rounded-lg object-contain"
                alt="资产图片"
              />
              <span
                class="absolute right-2 top-2 flex h-6 w-6 items-center justify-center rounded-full border bg-white shadow-sm"
                :class="isSelected(asset) ? 'border-primary text-primary' : 'border-slate-200 text-slate-300'"
              >
                <Check class="h-3.5 w-3.5" />
              </span>
              <span
                v-if="isExcluded(asset)"
                class="absolute inset-x-3 bottom-3 rounded-lg bg-slate-900/70 px-2 py-1 text-center text-xs font-bold text-white"
              >
                已在当前素材中
              </span>
            </div>
            <div class="space-y-1 p-3">
              <p class="truncate text-xs font-bold text-slate-700">{{ asset.title }}</p>
              <p class="truncate text-xs text-slate-400">{{ asset.createdAt }}</p>
            </div>
          </button>
        </div>
      </div>

      <div class="flex shrink-0 items-center justify-between border-t border-slate-100 bg-white px-5 py-3">
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="rounded-lg border border-slate-200 p-2 text-slate-500 disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="page <= 1"
            @click="changePage(page - 1)"
          >
            <ChevronLeft class="h-4 w-4" />
          </button>
          <span class="text-xs font-semibold text-slate-500">{{ page }} / {{ totalPages }}</span>
          <button
            type="button"
            class="rounded-lg border border-slate-200 p-2 text-slate-500 disabled:cursor-not-allowed disabled:opacity-40"
            :disabled="page >= totalPages"
            @click="changePage(page + 1)"
          >
            <ChevronRight class="h-4 w-4" />
          </button>
        </div>
        <div class="flex gap-2">
          <button
            type="button"
            class="rounded-lg border border-slate-200 px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-50"
            @click="emit('close')"
          >
            取消
          </button>
          <button
            type="button"
            class="rounded-lg bg-primary px-4 py-2 text-xs font-bold text-white disabled:cursor-not-allowed disabled:opacity-50"
            :disabled="selectedCount === 0"
            @click="confirmSelection"
          >
            添加 {{ selectedCount }} 个
          </button>
        </div>
      </div>
    </div>
  </AppModal>
</template>
