import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { createBillingOrder, getBillingOrder, getBillingPackages } from '@/api/billing.js'
import { useToast } from '@/composables/useToast.js'
import { useAuthStore } from '@/stores/auth.js'
import { getApiErrorMessage } from '@/utils/apiError.js'

const PAYMENT_POLL_TIMEOUT_MS = 10 * 60 * 1000

export function formatMoney(amountCents) {
  return `¥${(Number(amountCents || 0) / 100).toFixed(2)}`
}

export function formatCredits(credits) {
  return Number(credits || 0).toLocaleString('en-US')
}

export function useRechargeOrder(open) {
  const authStore = useAuthStore()
  const toast = useToast()
  const loadingPackages = ref(false)
  const mode = ref('packages')
  const packages = ref([])
  const selectedPackageId = ref('')
  const creatingOrder = ref(false)
  const currentOrder = ref(null)
  const qrDataUrl = ref('')
  const pollTimer = ref(null)
  const pollError = ref('')
  const pollStartedAt = ref(0)
  const paymentTimedOut = ref(false)
  const selectedPackage = computed(
    () => packages.value.find((item) => item.id === selectedPackageId.value) || null,
  )
  const modalTitle = computed(() => {
    if (currentOrder.value?.status === 'paid') return '充值成功'
    if (currentOrder.value?.status === 'failed') return '支付订单失败'
    if (paymentTimedOut.value) return '等待支付超时'
    return currentOrder.value ? '微信扫码支付' : '积分中心'
  })

  function clearPolling() {
    if (!pollTimer.value) return
    window.clearInterval(pollTimer.value)
    pollTimer.value = null
  }

  async function loadPackages() {
    loadingPackages.value = true
    try {
      const result = await getBillingPackages()
      if (result.code !== 0) return toast.error(result.message || '加载充值套餐失败')
      packages.value = result.data?.packages || []
      selectedPackageId.value = packages.value[0]?.id || ''
    } catch (error) {
      toast.error(getApiErrorMessage(error, '加载充值套餐失败'))
    } finally {
      loadingPackages.value = false
    }
  }

  async function refreshQr(order) {
    qrDataUrl.value = ''
    const source = order?.qrcode || order?.pay_url || ''
    if (!source || order?.img) return
    try {
      const { default: QRCode } = await import('qrcode')
      qrDataUrl.value = await QRCode.toDataURL(source, {
        width: 240,
        margin: 1,
        color: { dark: '#0f172a', light: '#ffffff' },
      })
    } catch {
      qrDataUrl.value = ''
    }
  }

  async function pollOrderOnce() {
    if (!currentOrder.value?.order_id) return
    if (pollStartedAt.value && Date.now() - pollStartedAt.value > PAYMENT_POLL_TIMEOUT_MS) {
      clearPolling()
      paymentTimedOut.value = true
      pollError.value = '等待支付超时，可重新创建订单或稍后再试。'
      return
    }
    try {
      const result = await getBillingOrder(currentOrder.value.order_id)
      if (result.code !== 0) return void (pollError.value = result.message || '订单状态查询失败')
      currentOrder.value = result.data
      pollError.value = ''
      if (result.data?.status === 'paid') {
        clearPolling()
        if (result.data?.credits !== undefined) authStore.updateCredits(result.data.credits)
        toast.success('充值成功，积分已到账')
      } else if (result.data?.status === 'failed') {
        clearPolling()
        pollError.value = result.data?.error_message || '支付订单失败，请重新创建订单。'
      }
    } catch {
      pollError.value = '订单状态查询失败'
    }
  }

  function startPolling() {
    clearPolling()
    pollStartedAt.value = Date.now()
    paymentTimedOut.value = false
    pollTimer.value = window.setInterval(pollOrderOnce, 2500)
  }

  async function createOrder() {
    if (!selectedPackage.value || creatingOrder.value) return
    creatingOrder.value = true
    try {
      const result = await createBillingOrder(selectedPackage.value.id)
      if (result.code !== 0) {
        if (result.data?.order_id) currentOrder.value = result.data
        return toast.error(result.message || '创建支付订单失败')
      }
      currentOrder.value = result.data
      await refreshQr(result.data)
      startPolling()
    } catch (error) {
      toast.error(getApiErrorMessage(error, '创建支付订单失败'))
    } finally {
      creatingOrder.value = false
    }
  }

  function resetToPackages() {
    clearPolling()
    mode.value = 'packages'
    currentOrder.value = null
    qrDataUrl.value = ''
    pollError.value = ''
    pollStartedAt.value = 0
    paymentTimedOut.value = false
  }

  watch(open, (visible) => (visible ? (resetToPackages(), loadPackages()) : clearPolling()), {
    immediate: true,
  })
  watch(currentOrder, refreshQr)
  onBeforeUnmount(clearPolling)

  return {
    authStore,
    loadingPackages,
    mode,
    packages,
    selectedPackageId,
    selectedPackage,
    creatingOrder,
    currentOrder,
    qrDataUrl,
    pollError,
    paymentTimedOut,
    modalTitle,
    clearPolling,
    createOrder,
    resetToPackages,
  }
}
