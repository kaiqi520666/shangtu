import {
  getAdminHeygenAvatars,
  syncAdminHeygenResources,
  updateAdminHeygenAvatar,
} from "@/api/admin.js";
import { useAdminHeygenResources } from "@/composables/admin/useAdminHeygenResources.js";

export function useAdminHeygenAvatars() {
  return useAdminHeygenResources({
    listApi: getAdminHeygenAvatars,
    updateApi: updateAdminHeygenAvatar,
    syncApi: syncAdminHeygenResources,
    defaultState: {
      gender: "",
      orientation: "",
      engine: "",
    },
    buildFilters: (state) => ({
      active: state.active || undefined,
      gender: state.gender || undefined,
      orientation: state.orientation || undefined,
      engine: state.engine || undefined,
    }),
    loadErrorMessage: "加载系统数字人失败",
    saveErrorMessage: "保存系统数字人失败",
    syncErrorMessage: "同步系统数字人失败",
    saveSuccessMessage: "系统数字人已保存",
    syncSuccessMessage: "HeyGen 系统数字人和声音已同步",
    enabledOnMessage: "系统数字人已启用",
    enabledOffMessage: "系统数字人已停用",
    nameRequiredMessage: "请填写数字人名称",
  });
}
