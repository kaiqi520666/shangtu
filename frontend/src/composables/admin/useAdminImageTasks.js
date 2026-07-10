import { reactive } from "vue";
import { getAdminImageTasks } from "@/api/admin.js";
import { createAdminPageState, useAdminPageLoader } from "@/composables/admin/useAdminPageState.js";
import { useToast } from "@/composables/useToast.js";

export function useAdminImageTasks() {
  const imageTasksState = reactive(createAdminPageState({ status: "", scenario: "", mediaType: "" }));
  const toast = useToast();
  const { loadPage, applyFilter, changePage } = useAdminPageLoader(toast);

  async function loadImageTasks() {
    await loadPage(
      imageTasksState,
      getAdminImageTasks,
      {
        status: imageTasksState.status || undefined,
        scenario: imageTasksState.scenario || undefined,
        media_type: imageTasksState.mediaType || undefined,
      },
      "加载生成任务失败",
    );
  }

  function applyImageTasksFilter() {
    applyFilter(imageTasksState, loadImageTasks);
  }

  return {
    imageTasksState,
    loadImageTasks,
    applyImageTasksFilter,
    changePage,
  };
}
