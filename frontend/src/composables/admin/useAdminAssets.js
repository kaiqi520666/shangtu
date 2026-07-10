import { computed, reactive, ref } from "vue";
import { getAdminAssets } from "@/api/admin.js";
import { createAdminPageState, useAdminPageLoader } from "@/composables/admin/useAdminPageState.js";
import { useCardActions } from "@/composables/useCardActions.js";
import { useToast } from "@/composables/useToast.js";
import { scenarioLabelMap } from "@/constants/scenarios.js";

export function mapAdminAsset(item) {
  return {
    id: item.id,
    taskId: item.id,
    dataUrl: item.result_url || "",
    resultUrl: item.result_url || "",
    previewUrl: item.result_url || "",
    title: item.title || "",
    typeId: item.type_id || "",
    scenario: item.scenario || "",
    mediaType: item.media_type || "image",
    jobTitle: item.job_title || "",
    userEmail: item.user_email || "",
    userId: item.user_id || "",
    createdAt: item.created_at || "",
    selected: false,
    status: item.status || "done",
  };
}

export function useAdminAssets() {
  const toast = useToast();
  const state = reactive(createAdminPageState({ scenario: "", mediaType: "" }));
  const currentTaskTitle = ref("管理资产");
  const assets = computed(() => state.items);
  const { loadPage, applyFilter, changePage } = useAdminPageLoader(toast);
  const actions = useCardActions({
    outputCards: assets,
    currentTaskTitle,
    getCardName: (card) => card.title || card.typeId || card.taskId || "asset",
    getDownloadUrl: (card) => card.resultUrl || card.dataUrl,
    getFetchHeaders: () => ({}),
    toast,
    mediaLabel: "资产",
    mediaUnit: "个",
    archiveName: "管理资产",
  });
  const allSelected = computed(() => state.items.length > 0 && state.items.every((card) => card.selected));

  async function listMappedAssets(params) {
    const result = await getAdminAssets(params);
    if (result.code !== 0) return result;
    return {
      ...result,
      data: {
        ...result.data,
        items: (result.data?.items || []).filter((item) => item.result_url).map(mapAdminAsset),
      },
    };
  }

  async function loadAssets() {
    await loadPage(
      state,
      listMappedAssets,
      {
        scenario: state.scenario || undefined,
        media_type: state.mediaType || undefined,
      },
      "加载管理资产失败",
    );
  }

  function applyAssetsFilter() {
    applyFilter(state, loadAssets);
  }

  function changeScenario(value) {
    state.scenario = value;
    applyAssetsFilter();
  }

  return {
    ...actions,
    allSelected,
    applyAssetsFilter,
    changePage: (direction) => changePage(state, loadAssets, direction),
    changeScenario,
    loadAssets,
    metaLabel: (card) => [card.userEmail, card.jobTitle || card.title].filter(Boolean).join(" · "),
    scenarioLabel: (card) => scenarioLabelMap[card.scenario] || "",
    state,
  };
}
