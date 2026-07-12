<script setup>
import { computed, onBeforeUnmount, ref, watch } from "vue";
import {
  CheckCircle2,
  CreditCard,
  ExternalLink,
  LoaderCircle,
  QrCode,
  RefreshCw,
  ShieldCheck,
  WalletCards,
} from "lucide-vue-next";
import { createBillingOrder, getBillingOrder, getBillingPackages } from "@/api/billing.js";
import AppModal from "@/components/ui/AppModal.vue";
import { useAuthStore } from "@/stores/auth.js";
import { useToast } from "@/composables/useToast.js";
import { getApiErrorMessage } from "@/utils/apiError.js";
import { multiplyCreditCosts } from "@/utils/creditPricing.js";

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["close"]);

const authStore = useAuthStore();
const toast = useToast();

const loadingPackages = ref(false);
const packages = ref([]);
const imageCreditCosts = ref({});
const videoCreditCosts = ref({});
const digitalHumanCreditCosts = ref({});
const digitalHumanPrechargeCosts = ref({});
const selectedPackageId = ref("");
const creatingOrder = ref(false);
const currentOrder = ref(null);
const qrDataUrl = ref("");
const pollTimer = ref(null);
const pollError = ref("");
const pollStartedAt = ref(0);
const paymentTimedOut = ref(false);

const PAYMENT_POLL_TIMEOUT_MS = 10 * 60 * 1000;

const selectedPackage = computed(
  () => packages.value.find((item) => item.id === selectedPackageId.value) || null,
);

const modalTitle = computed(() => {
  if (currentOrder.value?.status === "paid") return "充值成功";
  if (currentOrder.value?.status === "failed") return "支付订单失败";
  if (paymentTimedOut.value) return "等待支付超时";
  if (currentOrder.value) return "微信扫码支付";
  return "积分充值";
});

function formatMoney(amountCents) {
  return `¥${(Number(amountCents || 0) / 100).toFixed(2)}`;
}

function formatCredits(credits) {
  return Number(credits || 0).toLocaleString("en-US");
}

async function loadPackages() {
  loadingPackages.value = true;
  try {
    const result = await getBillingPackages();
    if (result.code !== 0) {
      toast.error(result.message || "加载充值套餐失败");
      return;
    }
    packages.value = result.data?.packages || [];
    imageCreditCosts.value = multiplyCreditCosts(result.data?.image_credit_costs, result.data?.consumption_multiplier, true);
    videoCreditCosts.value = multiplyCreditCosts(result.data?.video_credit_costs, result.data?.consumption_multiplier);
    digitalHumanCreditCosts.value = multiplyCreditCosts(result.data?.digital_human_credit_costs, result.data?.consumption_multiplier);
    digitalHumanPrechargeCosts.value = multiplyCreditCosts(result.data?.digital_human_precharge_costs, result.data?.consumption_multiplier, true);
    selectedPackageId.value = packages.value[0]?.id || "";
  } catch (error) {
    toast.error(getApiErrorMessage(error, "加载充值套餐失败"));
  } finally {
    loadingPackages.value = false;
  }
}

async function refreshQr(order) {
  qrDataUrl.value = "";
  const source = order?.qrcode || order?.pay_url || "";
  if (!source || order?.img) return;
  try {
    const { default: QRCode } = await import("qrcode");
    qrDataUrl.value = await QRCode.toDataURL(source, {
      width: 240,
      margin: 1,
      color: {
        dark: "#0f172a",
        light: "#ffffff",
      },
    });
  } catch {
    qrDataUrl.value = "";
  }
}

function clearPolling() {
  if (pollTimer.value) {
    window.clearInterval(pollTimer.value);
    pollTimer.value = null;
  }
}

async function pollOrderOnce() {
  if (!currentOrder.value?.order_id) return;
  if (pollStartedAt.value && Date.now() - pollStartedAt.value > PAYMENT_POLL_TIMEOUT_MS) {
    clearPolling();
    paymentTimedOut.value = true;
    pollError.value = "等待支付超时，可重新创建订单或稍后再试。";
    return;
  }
  try {
    const result = await getBillingOrder(currentOrder.value.order_id);
    if (result.code !== 0) {
      pollError.value = result.message || "订单状态查询失败";
      return;
    }
    currentOrder.value = result.data;
    pollError.value = "";
    if (result.data?.status === "paid") {
      clearPolling();
      if (result.data?.credits !== undefined) {
        authStore.updateCredits(result.data.credits);
      }
      toast.success("充值成功，积分已到账");
    } else if (result.data?.status === "failed") {
      clearPolling();
      pollError.value = result.data?.error_message || "支付订单失败，请重新创建订单。";
    }
  } catch {
    pollError.value = "订单状态查询失败";
  }
}

function startPolling() {
  clearPolling();
  pollStartedAt.value = Date.now();
  paymentTimedOut.value = false;
  pollTimer.value = window.setInterval(() => {
    pollOrderOnce();
  }, 2500);
}

async function createOrder() {
  if (!selectedPackage.value || creatingOrder.value) return;
  creatingOrder.value = true;
  try {
    const result = await createBillingOrder(selectedPackage.value.id);
    if (result.code !== 0) {
      if (result.data?.order_id) {
        currentOrder.value = result.data;
      }
      toast.error(result.message || "创建支付订单失败");
      return;
    }
    currentOrder.value = result.data;
    await refreshQr(result.data);
    startPolling();
  } catch (error) {
    toast.error(getApiErrorMessage(error, "创建支付订单失败"));
  } finally {
    creatingOrder.value = false;
  }
}

function resetToPackages() {
  clearPolling();
  currentOrder.value = null;
  qrDataUrl.value = "";
  pollError.value = "";
  pollStartedAt.value = 0;
  paymentTimedOut.value = false;
}

function closeModal() {
  clearPolling();
  emit("close");
}

watch(
  () => props.open,
  (visible) => {
    if (visible) {
      resetToPackages();
      loadPackages();
    } else {
      clearPolling();
    }
  },
);

watch(
  currentOrder,
  (order) => {
    refreshQr(order);
  },
  { deep: false },
);

onBeforeUnmount(() => {
  clearPolling();
});
</script>

<template>
  <AppModal
    :open="open"
    panel-class="w-full max-w-5xl border-slate-200/80 shadow-[0_28px_90px_rgba(15,23,42,0.32)]"
    @close="closeModal"
  >
    <template #header>
      <div class="flex min-w-0 items-center gap-3">
        <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-slate-950 text-emerald-300 shadow-sm">
          <WalletCards class="h-5 w-5" />
        </div>
        <div class="min-w-0">
          <h3 class="text-base font-black text-slate-950">{{ modalTitle }}</h3>
          <p class="mt-0.5 text-xs font-medium text-slate-500">积分实时到账，可用于图片和视频生成</p>
        </div>
      </div>
    </template>

    <div v-if="!currentOrder" class="min-h-0 space-y-3 overflow-y-auto bg-gradient-to-b from-slate-50/70 to-white p-4">
      <div class="rounded-2xl border border-emerald-100 bg-white px-4 py-3 shadow-[0_12px_32px_rgba(15,23,42,0.06)]">
        <div class="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div class="flex items-start gap-3">
            <div class="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 ring-1 ring-emerald-100">
              <ShieldCheck class="h-4 w-4" />
            </div>
            <div>
              <p class="text-xs font-black text-emerald-700">微信支付 · 实时到账</p>
              <p class="mt-0.5 text-xl font-black text-slate-950">当前 {{ formatCredits(authStore.credits) }} 点</p>
              <p class="mt-1 text-xs font-semibold text-slate-500">生成时自动扣积分，失败会退回。</p>
            </div>
          </div>
          <div class="grid gap-2 text-xs font-bold text-slate-600 sm:grid-cols-2 lg:w-[600px]">
            <div class="rounded-xl border border-slate-100 bg-slate-50/70 px-3 py-2.5">
              <p class="text-[11px] font-black text-slate-400">图片按张扣费</p>
              <div class="mt-1.5 flex flex-wrap gap-1.5">
                <span class="rounded-full bg-white px-2.5 py-1 text-slate-700 shadow-sm">1K {{ imageCreditCosts["1K"] || "-" }} 积分/张</span>
                <span class="rounded-full bg-white px-2.5 py-1 text-slate-700 shadow-sm">2K {{ imageCreditCosts["2K"] || "-" }} 积分/张</span>
                <span class="rounded-full bg-white px-2.5 py-1 text-slate-700 shadow-sm">4K {{ imageCreditCosts["4K"] || "-" }} 积分/张</span>
              </div>
            </div>
            <div class="rounded-xl border border-slate-100 bg-slate-50/70 px-3 py-2.5">
              <p class="text-[11px] font-black text-slate-400">视频按秒扣费</p>
              <div class="mt-1.5 flex flex-wrap gap-1.5">
                <span class="rounded-full bg-white px-2.5 py-1 text-slate-700 shadow-sm">720p {{ videoCreditCosts["720p"] || "-" }} 积分/秒</span>
                <span class="rounded-full bg-white px-2.5 py-1 text-slate-700 shadow-sm">1080p {{ videoCreditCosts["1080p"] || "-" }} 积分/秒</span>
              </div>
            </div>
            <div class="rounded-xl border border-slate-100 bg-slate-50/70 px-3 py-2.5 sm:col-span-2">
              <p class="text-[11px] font-black text-slate-400">数字人按档收费</p>
              <div class="mt-1.5 flex flex-wrap gap-1.5">
                <span class="rounded-full bg-white px-2.5 py-1 text-slate-700 shadow-sm">标准档 {{ digitalHumanCreditCosts.standard || "-" }} 积分/秒</span>
                <span class="rounded-full bg-white px-2.5 py-1 text-slate-700 shadow-sm">高质档 {{ digitalHumanCreditCosts.premium || "-" }} 积分/秒</span>
                <span class="rounded-full bg-white px-2.5 py-1 text-slate-700 shadow-sm">标准档预扣 {{ digitalHumanPrechargeCosts.standard || "-" }} 积分</span>
                <span class="rounded-full bg-white px-2.5 py-1 text-slate-700 shadow-sm">高质档预扣 {{ digitalHumanPrechargeCosts.premium || "-" }} 积分</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="loadingPackages" class="flex h-48 items-center justify-center text-sm text-slate-400">
        <LoaderCircle class="mr-2 h-4 w-4 animate-spin" />
        正在加载套餐...
      </div>

      <div v-else-if="packages.length" class="grid gap-2 sm:grid-cols-3">
        <button
          v-for="pkg in packages"
          :key="pkg.id"
          type="button"
          class="group relative flex min-h-[112px] flex-col items-center justify-center rounded-2xl border px-4 py-4 text-center transition-all duration-200"
          :class="selectedPackageId === pkg.id ? 'border-emerald-400 bg-emerald-50/80 text-slate-950 shadow-[0_14px_34px_rgba(16,185,129,0.16)] ring-1 ring-emerald-200' : 'border-slate-200 bg-white text-slate-950 shadow-sm hover:-translate-y-0.5 hover:border-emerald-200 hover:shadow-[0_14px_32px_rgba(15,23,42,0.10)]'"
          @click="selectedPackageId = pkg.id"
        >
          <CheckCircle2 v-if="selectedPackageId === pkg.id" class="absolute right-3 top-3 h-4 w-4 text-emerald-500" />
          <p class="text-xl font-black tracking-normal text-slate-950">{{ formatCredits(pkg.credits) }} 积分</p>
          <p class="mt-2 text-sm font-bold text-slate-500">{{ formatMoney(pkg.amount_cents) }}</p>
        </button>
      </div>

      <div v-else class="flex h-40 items-center justify-center rounded-2xl border border-dashed border-slate-200 text-sm font-semibold text-slate-400">
        暂无可用充值套餐
      </div>

      <button
        type="button"
        class="flex w-full items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 py-2.5 text-sm font-black text-white shadow-[0_12px_28px_rgba(15,23,42,0.20)] transition-colors hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
        :disabled="!selectedPackage || creatingOrder"
        @click="createOrder"
      >
        <LoaderCircle v-if="creatingOrder" class="h-4 w-4 animate-spin" />
        <CreditCard v-else class="h-4 w-4 text-emerald-300" />
        {{ creatingOrder ? "正在创建订单..." : selectedPackage ? `微信支付 ${formatMoney(selectedPackage.amount_cents)}` : "选择套餐" }}
      </button>
    </div>

    <div v-else-if="currentOrder.status === 'paid'" class="flex flex-col items-center gap-4 bg-white p-8 text-center">
      <div class="flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-600">
        <CheckCircle2 class="h-9 w-9" />
      </div>
      <div>
        <h3 class="text-lg font-black text-slate-950">充值成功</h3>
        <p class="mt-1 text-sm text-slate-500">
          已到账 {{ currentOrder.credits_to_add }} 点，当前余额 {{ authStore.credits }} 点
        </p>
      </div>
      <button type="button" class="rounded-xl bg-slate-950 px-5 py-2.5 text-sm font-bold text-white hover:bg-slate-800" @click="closeModal">
        完成
      </button>
    </div>

    <div v-else-if="currentOrder.status === 'failed' || paymentTimedOut" class="flex flex-col items-center gap-4 bg-white p-8 text-center">
      <div class="flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-100 text-slate-400">
        <RefreshCw class="h-8 w-8" />
      </div>
      <div>
        <h3 class="text-lg font-black text-slate-950">{{ paymentTimedOut ? "等待支付超时" : "支付订单失败" }}</h3>
        <p class="mt-1 text-sm text-slate-500">
          {{ pollError || currentOrder.error_message || "请更换套餐或重新创建支付订单。" }}
        </p>
      </div>
      <button type="button" class="rounded-xl bg-slate-950 px-5 py-2.5 text-sm font-bold text-white hover:bg-slate-800" @click="resetToPackages">
        重新选择套餐
      </button>
    </div>

    <div v-else class="grid gap-6 bg-white p-5 sm:p-6 md:grid-cols-[280px_1fr]">
      <div class="flex flex-col items-center rounded-2xl border border-slate-200 bg-slate-50 p-5">
        <div class="mb-4 inline-flex items-center gap-2 rounded-full bg-white px-3 py-1 text-[11px] font-black text-slate-600 shadow-sm">
          <QrCode class="h-3.5 w-3.5 text-emerald-600" />
          微信扫码支付
        </div>
        <div class="flex h-60 w-60 items-center justify-center rounded-2xl border border-slate-200 bg-white p-3 shadow-inner">
          <img v-if="currentOrder.img" :src="currentOrder.img" class="h-full w-full object-contain" alt="微信支付二维码" />
          <img v-else-if="qrDataUrl" :src="qrDataUrl" class="h-full w-full object-contain" alt="微信支付二维码" />
          <LoaderCircle v-else class="h-6 w-6 animate-spin text-slate-300" />
        </div>
        <p class="mt-3 text-xs font-semibold text-slate-500">支付成功后自动到账</p>
      </div>

      <div class="flex flex-col justify-between gap-5">
        <div class="space-y-3">
          <div class="rounded-2xl border border-slate-200 bg-white p-4">
            <p class="text-xs text-slate-400">订单号</p>
            <p class="mt-1 break-all text-xs font-bold text-slate-700">{{ currentOrder.out_trade_no }}</p>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div class="rounded-2xl border border-slate-200 bg-white p-4">
              <p class="text-xs text-slate-400">充值积分</p>
              <p class="mt-1 text-lg font-black text-emerald-600">{{ currentOrder.credits_to_add }} 点</p>
            </div>
            <div class="rounded-2xl border border-slate-200 bg-white p-4">
              <p class="text-xs text-slate-400">支付金额</p>
              <p class="mt-1 text-lg font-black text-slate-950">{{ formatMoney(currentOrder.amount_cents) }}</p>
            </div>
          </div>
          <p class="rounded-xl bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700">
            支付成功后会自动到账；如果页面未更新，请稍等几秒。
          </p>
          <p v-if="pollError" class="rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-600">{{ pollError }}</p>
        </div>

        <div class="flex gap-2">
          <a
            v-if="currentOrder.pay_url || currentOrder.qrcode"
            :href="currentOrder.pay_url || currentOrder.qrcode"
            target="_blank"
            rel="noreferrer"
            class="flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-slate-200 px-3 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-50"
          >
            <ExternalLink class="h-4 w-4" />
            打开支付页
          </a>
          <button
            type="button"
            class="flex flex-1 items-center justify-center gap-1.5 rounded-xl border border-slate-200 px-3 py-2.5 text-xs font-bold text-slate-700 hover:bg-slate-50"
            @click="resetToPackages"
          >
            <RefreshCw class="h-4 w-4" />
            更换套餐
          </button>
        </div>
      </div>
    </div>
  </AppModal>
</template>
