import { computed, ref } from "vue";
import { defineStore } from "pinia";
import { getImageCatalog } from "@/api/image.js";

function normalizeCatalogItem(item) {
  const id = item?.id || "";
  const name = item?.name || id;
  const desc = item?.desc || "";
  const strategy = item?.strategy || "";
  const defaultCount = Number(item?.default_count ?? 1);
  const maxCount = Number(item?.max_count ?? defaultCount);
  return {
    id,
    name,
    label: name,
    desc,
    description: desc,
    strategy,
    defaultCount: Number.isFinite(defaultCount) && defaultCount > 0 ? defaultCount : 1,
    maxCount: Number.isFinite(maxCount) && maxCount > 0 ? maxCount : 1,
  };
}

function normalizeCatalogList(items) {
  if (!Array.isArray(items)) return [];
  return items.map(normalizeCatalogItem).filter((item) => item.id);
}

export const useCatalogStore = defineStore("catalog", () => {
  const loaded = ref(false);
  const loading = ref(false);
  const loadError = ref("");
  const productImage = ref([]);
  const productSuite = ref([]);
  const outfit = ref([]);
  let loadingPromise = null;

  const modules = computed(() => productImage.value);
  const suiteStructures = computed(() => productSuite.value);
  const outfitScenes = computed(() => outfit.value);

  async function ensureLoaded() {
    if (loaded.value) return;
    if (loadingPromise) return loadingPromise;

    return loadCatalog();
  }

  async function reload() {
    loaded.value = false;
    return loadCatalog();
  }

  async function loadCatalog() {
    if (loadingPromise) return loadingPromise;
    loading.value = true;
    loadError.value = "";
    loadingPromise = getImageCatalog()
      .then((result) => {
        if (result.code !== 0) {
          throw new Error(result.message || "目录加载失败");
        }
        const data = result.data || {};
        productImage.value = normalizeCatalogList(data.product_image);
        productSuite.value = normalizeCatalogList(data.product_suite);
        outfit.value = normalizeCatalogList(data.outfit);
        loaded.value = true;
      })
      .catch((error) => {
        loadError.value = error.response?.data?.message || error.message || "目录加载失败";
        throw error;
      })
      .finally(() => {
        loading.value = false;
        loadingPromise = null;
      });

    return loadingPromise;
  }

  function findModule(id) {
    return modules.value.find((item) => item.id === id) || null;
  }

  function findSuiteStructure(id) {
    return suiteStructures.value.find((item) => item.id === id) || null;
  }

  function findOutfitScene(id) {
    return outfitScenes.value.find((item) => item.id === id) || null;
  }

  return {
    loaded,
    loading,
    loadError,
    productImage,
    productSuite,
    outfit,
    modules,
    suiteStructures,
    outfitScenes,
    ensureLoaded,
    reload,
    findModule,
    findSuiteStructure,
    findOutfitScene,
  };
});
