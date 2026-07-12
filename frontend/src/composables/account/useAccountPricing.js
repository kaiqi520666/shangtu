import { computed, ref } from "vue";
import { getAccountPricing } from "@/api/account.js";
import { useToast } from "@/composables/useToast.js";
import { getApiErrorMessage } from "@/utils/apiError.js";
import { applyConsumptionMultiplier, multiplyCreditCosts } from "@/utils/creditPricing.js";

export function useAccountPricing() {
  const pricing = ref(null);
  const loading = ref(false);
  const toast = useToast();

  const adjusted = computed(() => {
    const data = pricing.value;
    if (!data) return null;
    const multiplier = Number(data.consumption_multiplier || 1);
    return {
      multiplier,
      image: multiplyCreditCosts(data.image_credit_costs, multiplier, true),
      video: multiplyCreditCosts(data.video_credit_costs, multiplier),
      digitalHuman: multiplyCreditCosts(data.digital_human_credit_costs, multiplier),
      digitalHumanPrecharge: multiplyCreditCosts(data.digital_human_precharge_costs, multiplier, true),
      videoTranslation: multiplyCreditCosts(data.video_translation_credit_costs, multiplier),
      voiceover: applyConsumptionMultiplier(data.voiceover_credit_cost_per_100_chars, multiplier),
    };
  });

  async function loadPricing() {
    loading.value = true;
    try {
      const result = await getAccountPricing();
      if (result.code !== 0) return toast.error(result.message || "加载计费标准失败");
      pricing.value = result.data;
    } catch (error) {
      toast.error(getApiErrorMessage(error, "加载计费标准失败"));
    } finally {
      loading.value = false;
    }
  }

  return { adjusted, loading, loadPricing };
}
