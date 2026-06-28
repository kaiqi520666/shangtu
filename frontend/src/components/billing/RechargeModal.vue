<script setup>
import { computed, onBeforeUnmount, ref, watch } from "vue";
import QRCode from "qrcode";
import { CheckCircle2, ExternalLink, LoaderCircle, RefreshCw, WalletCards } from "lucide-vue-next";
import { createBillingOrder, getBillingOrder, getBillingPackages } from "@/api/billing.js";
import AppModal from "@/components/ui/AppModal.vue";
import { useAuthStore } from "@/stores/auth.js";
import { useToast } from "@/composables/useToast.js";
import { getApiErrorMessage } from "@/utils/apiError.js";

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

function imageCountText(pkg, quality) {
  const unit = Number(imageCreditCosts.value?.[quality] || 0);
  if (!unit) return "-";
  return Math.floor(Number(pkg.credits || 0) / unit);
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
    imageCreditCosts.value = result.data?.image_credit_costs || {};
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
    :title="modalTitle"
    subtitle="充值后积分实时到账，可用于 1K / 2K / 4K 生图"
    panel-class="w-full max-w-2xl"
    @close="closeModal"
  >
    <div v-if="!currentOrder" class="space-y-5 p-5">
      <div class="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-4 py-3">
        <div class="flex items-center gap-2 text-sm font-bold text-slate-800">
          <WalletCards class="h-4 w-4 text-primary" />
          当前余额
        </div>
        <span class="text-sm font-bold text-primary">{{ authStore.credits }} 点</span>
      </div>

      <div v-if="loadingPackages" class="flex h-48 items-center justify-center text-sm text-slate-400">
        <LoaderCircle class="mr-2 h-4 w-4 animate-spin" />
        正在加载套餐...
      </div>

      <div v-else-if="packages.length" class="grid gap-3 sm:grid-cols-3">
        <button
          v-for="pkg in packages"
          :key="pkg.id"
          type="button"
          class="relative rounded-xl border p-4 text-left transition-all"
          :class="selectedPackageId === pkg.id ? 'border-primary bg-primary/5 ring-2 ring-primary/10' : 'border-slate-200 bg-white hover:border-primary/30'"
          @click="selectedPackageId = pkg.id"
        >
          <span v-if="pkg.badge" class="absolute right-3 top-3 rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-bold text-primary">
            {{ pkg.badge }}
          </span>
          <p class="text-sm font-bold text-slate-900">{{ pkg.name }}</p>
          <p class="mt-2 text-2xl font-black text-primary">{{ pkg.credits }}</p>
          <p class="text-xs font-semibold text-slate-400">积分</p>
          <p class="mt-3 text-sm font-bold text-slate-800">{{ formatMoney(pkg.amount_cents) }}</p>
          <div class="mt-3 space-y-1 text-[11px] text-slate-500">
            <p>约 {{ imageCountText(pkg, "1K") }} 张 1K</p>
            <p>约 {{ imageCountText(pkg, "2K") }} 张 2K</p>
            <p>约 {{ imageCountText(pkg, "4K") }} 张 4K</p>
          </div>
        </button>
      </div>

      <div v-else class="flex h-40 items-center justify-center rounded-xl border border-dashed border-slate-200 text-sm font-semibold text-slate-400">
        暂无可用充值套餐
      </div>

      <button
        type="button"
        class="flex w-full items-center justify-center gap-2 rounded-xl bg-primary px-4 py-3 text-sm font-bold text-white shadow-sm transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
        :disabled="!selectedPackage || creatingOrder"
        @click="createOrder"
      >
        <LoaderCircle v-if="creatingOrder" class="h-4 w-4 animate-spin" />
        {{ creatingOrder ? "正在创建订单..." : "微信支付" }}
      </button>
    </div>

    <div v-else-if="currentOrder.status === 'paid'" class="flex flex-col items-center gap-4 p-8 text-center">
      <CheckCircle2 class="h-14 w-14 text-primary" />
      <div>
        <h3 class="text-lg font-bold text-slate-900">充值成功</h3>
        <p class="mt-1 text-sm text-slate-500">
          已到账 {{ currentOrder.credits_to_add }} 点，当前余额 {{ authStore.credits }} 点
        </p>
      </div>
      <button type="button" class="rounded-xl bg-primary px-5 py-2.5 text-sm font-bold text-white" @click="closeModal">
        完成
      </button>
    </div>

    <div v-else-if="currentOrder.status === 'failed' || paymentTimedOut" class="flex flex-col items-center gap-4 p-8 text-center">
      <RefreshCw class="h-12 w-12 text-slate-300" />
      <div>
        <h3 class="text-lg font-bold text-slate-900">{{ paymentTimedOut ? "等待支付超时" : "支付订单失败" }}</h3>
        <p class="mt-1 text-sm text-slate-500">
          {{ pollError || currentOrder.error_message || "请更换套餐或重新创建支付订单。" }}
        </p>
      </div>
      <button type="button" class="rounded-xl bg-primary px-5 py-2.5 text-sm font-bold text-white" @click="resetToPackages">
        重新选择套餐
      </button>
    </div>

    <div v-else class="grid gap-6 p-5 md:grid-cols-[280px_1fr]">
      <div class="flex flex-col items-center rounded-xl border border-slate-200 bg-slate-50 p-5">
        <div class="flex h-60 w-60 items-center justify-center rounded-xl border border-slate-200 bg-white p-3 shadow-inner">
          <img v-if="currentOrder.img" :src="currentOrder.img" class="h-full w-full object-contain" alt="微信支付二维码" />
          <img v-else-if="qrDataUrl" :src="qrDataUrl" class="h-full w-full object-contain" alt="微信支付二维码" />
          <LoaderCircle v-else class="h-6 w-6 animate-spin text-slate-300" />
        </div>
        <p class="mt-3 text-xs font-semibold text-slate-500">请使用微信扫码支付</p>
      </div>

      <div class="flex flex-col justify-between gap-5">
        <div class="space-y-3">
          <div class="rounded-xl border border-slate-200 p-4">
            <p class="text-xs text-slate-400">订单号</p>
            <p class="mt-1 break-all text-xs font-bold text-slate-700">{{ currentOrder.out_trade_no }}</p>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div class="rounded-xl border border-slate-200 p-4">
              <p class="text-xs text-slate-400">充值积分</p>
              <p class="mt-1 text-lg font-black text-primary">{{ currentOrder.credits_to_add }} 点</p>
            </div>
            <div class="rounded-xl border border-slate-200 p-4">
              <p class="text-xs text-slate-400">支付金额</p>
              <p class="mt-1 text-lg font-black text-slate-900">{{ formatMoney(currentOrder.amount_cents) }}</p>
            </div>
          </div>
          <p class="rounded-lg bg-sky-50 px-3 py-2 text-xs text-sky-600">
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
