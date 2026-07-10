import { computed, ref } from "vue";
import { getDigitalHumanConfig } from "@/api/digitalHuman.js";
import { useToast } from "@/composables/useToast.js";

const DEFAULT_PRECHARGE_COSTS = {
  standard: 2000,
  premium: 5000,
};

const DEFAULT_CREDIT_COSTS = {
  standard: 7,
  premium: 16,
};

const pricingState = {
  creditCosts: ref({ ...DEFAULT_CREDIT_COSTS }),
  prechargeCosts: ref({ ...DEFAULT_PRECHARGE_COSTS }),
  loading: ref(false),
  loaded: ref(false),
};

export function useDigitalHumanPricing() {
  const toast = useToast();

  async function loadPricing() {
    if (pricingState.loading.value) return;
    pricingState.loading.value = true;
    try {
      const result = await getDigitalHumanConfig();
      if (result.code !== 0) {
        toast.error(result.message || "加载数字人价格失败");
        return;
      }
      pricingState.creditCosts.value = {
        ...DEFAULT_CREDIT_COSTS,
        ...result.data?.credit_costs,
      };
      pricingState.prechargeCosts.value = {
        ...DEFAULT_PRECHARGE_COSTS,
        ...result.data?.precharge_costs,
      };
      pricingState.loaded.value = true;
    } catch {
      toast.error("加载数字人价格失败");
    } finally {
      pricingState.loading.value = false;
    }
  }

  const qualityOptions = computed(() => [
    {
      value: "standard",
      label: "标准档",
      description: `日常口播 · ${pricingState.creditCosts.value.standard || DEFAULT_CREDIT_COSTS.standard}积分/秒 · 预扣 ${pricingState.prechargeCosts.value.standard || DEFAULT_PRECHARGE_COSTS.standard}积分`,
    },
    {
      value: "premium",
      label: "高质档",
      description: `更高表现力 · ${pricingState.creditCosts.value.premium || DEFAULT_CREDIT_COSTS.premium}积分/秒 · 预扣 ${pricingState.prechargeCosts.value.premium || DEFAULT_PRECHARGE_COSTS.premium}积分`,
    },
  ]);

  return {
    creditCosts: pricingState.creditCosts,
    prechargeCosts: pricingState.prechargeCosts,
    pricingLoading: pricingState.loading,
    pricingLoaded: pricingState.loaded,
    qualityOptions,
    loadPricing,
  };
}
