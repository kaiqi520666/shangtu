import { computed, ref } from "vue";
import { Ban, CheckCircle2, Coins, ReceiptText, UsersRound } from "lucide-vue-next";
import { getAdminOverview } from "@/api/admin.js";
import { formatMoney } from "@/constants/admin.js";
import { useToast } from "@/composables/useToast.js";

const overview = ref(null);
const overviewLoading = ref(false);

const overviewCards = computed(() => {
  const data = overview.value || {};
  return [
    { label: "用户总数", value: data.total_users || 0, icon: UsersRound },
    { label: "今日新增", value: data.today_new_users || 0, icon: CheckCircle2 },
    { label: "累计充值", value: formatMoney(data.paid_amount_cents || 0), icon: ReceiptText },
    { label: "今日充值", value: formatMoney(data.today_paid_amount_cents || 0), icon: Coins },
    { label: "总积分余额", value: `${data.total_credit_balance || 0} 点`, icon: Coins },
    { label: "失败任务", value: data.failed_image_tasks || 0, icon: Ban },
  ];
});

export function useAdminOverview() {
  const toast = useToast();

  async function loadOverview() {
    overviewLoading.value = true;
    try {
      const result = await getAdminOverview();
      if (result.code !== 0) {
        toast.error(result.message || "加载概览失败");
        return;
      }
      overview.value = result.data || {};
    } catch {
      toast.error("加载概览失败");
    } finally {
      overviewLoading.value = false;
    }
  }

  return {
    overviewCards,
    overviewLoading,
    loadOverview,
  };
}
