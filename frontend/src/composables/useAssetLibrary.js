import { computed, ref } from "vue";
import { useToast } from "@/composables/useToast.js";
import { useCardActions } from "@/composables/useCardActions.js";
import { listAssets, deleteAssets } from "@/api/assets.js";
import { getImageDownloadUrl } from "@/api/image.js";
import { getVideoDownloadUrl } from "@/api/video.js";

const SCENARIO_OPTIONS = [
  { value: "", label: "全部" },
  { value: "product_suite", label: "商品套图" },
  { value: "product_image", label: "商品详情图" },
  { value: "outfit", label: "服饰穿搭" },
  { value: "free_image", label: "自由生图" },
  { value: "product_video", label: "商品视频" },
];

export function useAssetLibrary() {
  const toast = useToast();
  const assets = ref([]);
  const loading = ref(false);
  const total = ref(0);
  const page = ref(1);
  const pageSize = ref(20);
  const scenario = ref("");
  const currentTaskTitle = ref("资产库");

  const totalPages = computed(() => Math.ceil(total.value / pageSize.value) || 1);

  const actions = useCardActions({
    outputCards: assets,
    currentTaskTitle,
    getCardName: (card) => card.title || card.typeId || "asset",
    getDownloadUrl: (card) =>
      card.mediaType === "video"
        ? getVideoDownloadUrl(card.taskId)
        : getImageDownloadUrl(card.taskId),
    mediaLabel: "资产",
    mediaUnit: "个",
    archiveName: "资产库",
    toast,
  });

  const {
    zoomCard,
    selectedCards,
    selectedCardsCount,
    toggleCardSelection,
    toggleSelectAllCards,
    batchDownload,
    downloadSingleMedia: downloadAsset,
  } = actions;

  async function loadAssets() {
    loading.value = true;
    try {
      const result = await listAssets({
        scenario: scenario.value,
        page: page.value,
        page_size: pageSize.value,
      });
      if (result.code !== 0) {
        toast.error(result.message || "加载资产列表失败");
        assets.value = [];
        total.value = 0;
        return;
      }
      const data = result.data || {};
      total.value = data.total || 0;
      // 映射为资产卡片统一字段，图片和视频共用同一套选择/预览逻辑。
      assets.value = (data.items || []).map((item) => ({
        id: item.task_id,
        taskId: item.task_id,
        dataUrl: item.result_url || "",
        resultUrl: item.result_url || "",
        title: item.title || "",
        typeId: item.type_id || "",
        scenario: item.scenario || "",
        mediaType: item.media_type || "image",
        jobTitle: item.job_title || "",
        createdAt: item.created_at || "",
        selected: false,
        status: "done",
      }));
    } catch (error) {
      const status = error.response?.status;
      if (status === 401) {
        toast.error("登录已过期，请重新登录");
      } else {
        toast.error(error.response?.data?.message || "加载资产列表失败");
      }
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

  function changePage(p) {
    if (p < 1 || p > totalPages.value) return;
    page.value = p;
    loadAssets();
  }

  async function deleteSelected() {
    const ids = selectedCards.value.map((card) => card.taskId);
    if (ids.length === 0) {
      toast.info("请先选择要删除的资产");
      return false;
    }
    try {
      const mediaTypes = [...new Set(selectedCards.value.map((card) => card.mediaType || "image"))];
      const result = await deleteAssets(ids, mediaTypes.length === 1 ? mediaTypes[0] : "");
      if (result.code !== 0) {
        toast.error(result.message || "删除失败");
        return false;
      }
      const deletedCount = result.data?.deleted || 0;
      toast.success(`已删除 ${deletedCount} 个资产`);
      // 刷新当前页（如果删完了当前页，回退一页）
      if (assets.value.length === deletedCount && page.value > 1) {
        page.value -= 1;
      }
      await loadAssets();
      return true;
    } catch (error) {
      const status = error.response?.status;
      if (status === 401) {
        toast.error("登录已过期，请重新登录");
      } else {
        toast.error(error.response?.data?.message || "删除失败");
      }
      return false;
    }
  }

  return {
    // 状态
    assets,
    loading,
    total,
    page,
    pageSize,
    scenario,
    totalPages,
    // 选择/下载
    zoomCard,
    selectedCards,
    selectedCardsCount,
    toggleCardSelection,
    toggleSelectAllCards,
    batchDownload,
    downloadAsset,
    // 操作
    loadAssets,
    changeScenario,
    changePage,
    deleteSelected,
    // 常量
    SCENARIO_OPTIONS,
  };
}
