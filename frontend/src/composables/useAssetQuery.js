import { computed, ref } from "vue";
import { listAssets } from "@/api/assets.js";
import { generationScenarios, scenarioOptions } from "@/constants/scenarios.js";

export const assetMediaTypeOptions = [
  { value: "", label: "全部" },
  { value: "image", label: "图片" },
  { value: "video", label: "视频" },
  { value: "audio", label: "音频" },
];

export function mapAssetItem(item) {
  const resultUrl = item.result_url || "";
  return {
    id: item.task_id,
    taskId: item.task_id,
    url: resultUrl,
    dataUrl: item.thumb_url || resultUrl,
    resultUrl,
    thumbUrl: item.thumb_url || resultUrl,
    previewUrl: item.preview_url || resultUrl,
    title: item.title || item.job_title || "资产",
    typeId: item.type_id || "",
    scenario: item.scenario || "",
    mediaType: item.media_type || "image",
    source: item.source || "generated",
    durationSeconds: item.duration_seconds || 0,
    size: item.size || 0,
    contentType: item.content_type || "",
    jobTitle: item.job_title || "",
    createdAt: item.created_at || "",
    selected: false,
    status: "done",
  };
}

export function useAssetQuery({ initialMediaType = "", pageSize: initialPageSize = 20, onError } = {}) {
  const assets = ref([]);
  const loading = ref(false);
  const total = ref(0);
  const page = ref(1);
  const pageSize = ref(initialPageSize);
  const mediaType = ref(initialMediaType);
  const scenario = ref("");

  const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)));
  const scenarioFilters = computed(() => {
    if (mediaType.value === "audio") return [];
    if (!mediaType.value) return scenarioOptions;
    return scenarioOptions.filter(
      (option) => !option.value || generationScenarios.find((item) => item.value === option.value)?.mediaType === mediaType.value,
    );
  });

  function reportError(message) {
    onError?.(message);
  }

  function resetIncompatibleScenario() {
    if (scenario.value && !scenarioFilters.value.some((option) => option.value === scenario.value)) {
      scenario.value = "";
    }
  }

  async function loadAssets() {
    loading.value = true;
    try {
      const result = await listAssets({
        scenario: scenario.value,
        media_type: mediaType.value,
        page: page.value,
        page_size: pageSize.value,
      });
      if (result.code !== 0) {
        reportError(result.message || "资产加载失败");
        assets.value = [];
        total.value = 0;
        return false;
      }
      const data = result.data || {};
      total.value = data.total || 0;
      assets.value = (data.items || []).map(mapAssetItem);
      return true;
    } catch (error) {
      reportError(error.response?.data?.message || "资产加载失败");
      assets.value = [];
      total.value = 0;
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function changeMediaType(value) {
    mediaType.value = value;
    resetIncompatibleScenario();
    page.value = 1;
    await loadAssets();
  }

  async function changeScenario(value) {
    scenario.value = value;
    page.value = 1;
    await loadAssets();
  }

  async function changePage(nextPage) {
    if (nextPage < 1 || nextPage > totalPages.value) return;
    page.value = nextPage;
    await loadAssets();
  }

  return {
    assets,
    loading,
    total,
    page,
    pageSize,
    mediaType,
    scenario,
    totalPages,
    scenarioFilters,
    loadAssets,
    changeMediaType,
    changeScenario,
    changePage,
  };
}
