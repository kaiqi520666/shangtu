import {
  getAdminHeygenVoices,
  syncAdminHeygenResources,
  updateAdminHeygenVoice,
} from "@/api/admin.js";
import { useAdminHeygenResources } from "@/composables/admin/useAdminHeygenResources.js";

export function useAdminHeygenVoices() {
  return useAdminHeygenResources({
    listApi: getAdminHeygenVoices,
    updateApi: updateAdminHeygenVoice,
    syncApi: syncAdminHeygenResources,
    defaultState: {
      gender: "",
      language: "",
      support_locale: "",
      support_pause: "",
    },
    buildFilters: (state) => ({
      active: state.active || undefined,
      gender: state.gender || undefined,
      language: state.language || undefined,
      support_locale: state.support_locale || undefined,
      support_pause: state.support_pause || undefined,
    }),
    loadErrorMessage: "加载系统声音失败",
    saveErrorMessage: "保存系统声音失败",
    syncErrorMessage: "同步系统声音失败",
    saveSuccessMessage: "系统声音已保存",
    syncSuccessMessage: "HeyGen 系统数字人和声音已同步",
    enabledOnMessage: "系统声音已启用",
    enabledOffMessage: "系统声音已停用",
    nameRequiredMessage: "请填写声音名称",
  });
}
