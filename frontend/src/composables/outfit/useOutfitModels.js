import { computed, ref } from "vue";
import { deleteOutfitModel, listOutfitModels, uploadOutfitModel } from "@/api/outfit.js";
import { getApiErrorMessage } from "@/utils/apiError.js";

export function normalizeOutfitModel(model) {
  return {
    id: model.id,
    name: model.name,
    image: model.image_url,
    objectKey: model.object_key,
    sortOrder: model.sort_order || 0,
    isSystem: Boolean(model.is_system),
    canDelete: Boolean(model.can_delete),
    createdAt: model.created_at || "",
  };
}

export function useOutfitModels({ toast }) {
  const modelLibrary = ref([]);
  const modelsLoading = ref(false);
  const modelUploading = ref(false);
  const modelDeletingId = ref("");
  const selectedModelId = ref("");
  const restoredModelSnapshot = ref(null);
  const selectedModel = computed(() =>
    modelLibrary.value.find((model) => model.id === selectedModelId.value) ||
    (restoredModelSnapshot.value?.id === selectedModelId.value ? restoredModelSnapshot.value : null),
  );

  async function loadOutfitModels() {
    modelsLoading.value = true;
    try {
      const result = await listOutfitModels();
      if (result.code !== 0) {
        toast.error(result.message || "加载模特失败");
        modelLibrary.value = [];
        selectedModelId.value = "";
        return;
      }
      modelLibrary.value = (result.data || []).map(normalizeOutfitModel);
      if (!selectedModel.value && modelLibrary.value.length > 0) {
        selectedModelId.value = modelLibrary.value[0].id;
      }
    } catch (error) {
      toast.error(getApiErrorMessage(error, "加载模特失败"));
      modelLibrary.value = [];
      selectedModelId.value = "";
    } finally {
      modelsLoading.value = false;
    }
  }

  async function uploadModel(file) {
    if (!file) return;
    modelUploading.value = true;
    try {
      const result = await uploadOutfitModel(file);
      if (result.code !== 0) {
        toast.error(result.message || "模特上传失败");
        return;
      }
      const model = normalizeOutfitModel(result.data);
      modelLibrary.value = [model, ...modelLibrary.value];
      selectedModelId.value = model.id;
      toast.success("模特已上传");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "模特上传失败"));
    } finally {
      modelUploading.value = false;
    }
  }

  async function deleteModel(modelId) {
    const model = modelLibrary.value.find((item) => item.id === modelId);
    if (!model || !model.canDelete) {
      toast.info("系统默认模特不能删除");
      return;
    }
    modelDeletingId.value = modelId;
    try {
      const result = await deleteOutfitModel(modelId);
      if (result.code !== 0) {
        toast.error(result.message || "删除模特失败");
        return;
      }
      modelLibrary.value = modelLibrary.value.filter((item) => item.id !== modelId);
      if (selectedModelId.value === modelId) selectedModelId.value = modelLibrary.value[0]?.id || "";
      toast.success("模特已删除");
    } catch (error) {
      toast.error(getApiErrorMessage(error, "删除模特失败"));
    } finally {
      modelDeletingId.value = "";
    }
  }

  return {
    deleteModel,
    loadOutfitModels,
    modelDeletingId,
    modelLibrary,
    modelUploading,
    modelsLoading,
    restoredModelSnapshot,
    selectedModel,
    selectedModelId,
    uploadModel,
  };
}
