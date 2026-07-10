import { ref } from "vue";
import { useToast } from "@/composables/useToast.js";
import { useCardActions } from "@/composables/useCardActions.js";
import { deleteAssets, getAssetDownloadUrl } from "@/api/assets.js";
import { assetMediaTypeOptions, useAssetQuery } from "@/composables/useAssetQuery.js";

export function useAssetLibrary() {
  const toast = useToast();
  const currentTaskTitle = ref("资产库");
  const query = useAssetQuery({ onError: (message) => toast.error(message || "加载资产列表失败") });
  const { assets, loading, total, page, pageSize, mediaType, scenario, totalPages, scenarioFilters } = query;

  const actions = useCardActions({
    outputCards: assets,
    currentTaskTitle,
    getCardName: (card) => card.title || card.typeId || "asset",
    getDownloadUrl: (card) => getAssetDownloadUrl(card.mediaType, card.taskId),
    mediaLabel: "资产",
    mediaUnit: "个",
    archiveName: "资产库",
    toast,
  });

  const {
    zoomCard,
    downloading,
    selectedCards,
    selectedCardsCount,
    toggleCardSelection,
    toggleSelectAllCards,
    batchDownload,
    downloadSingleMedia: downloadAsset,
  } = actions;

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
      await query.loadAssets();
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
    mediaType,
    scenario,
    totalPages,
    scenarioFilters,
    // 选择/下载
    zoomCard,
    downloading,
    selectedCards,
    selectedCardsCount,
    toggleCardSelection,
    toggleSelectAllCards,
    batchDownload,
    downloadAsset,
    // 操作
    loadAssets: query.loadAssets,
    changeMediaType: query.changeMediaType,
    changeScenario: query.changeScenario,
    changePage: query.changePage,
    deleteSelected,
    // 常量
    mediaTypeOptions: assetMediaTypeOptions,
  };
}
