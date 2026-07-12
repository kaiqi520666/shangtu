<script setup>
import { onMounted } from "vue";
import AdminCouponCodesPanel from "@/components/admin/coupons/AdminCouponCodesPanel.vue";
import CouponCodeModal from "@/components/admin/coupons/CouponCodeModal.vue";
import { useAdminCouponCodes } from "@/composables/admin/useAdminCouponCodes.js";

const couponCodes = useAdminCouponCodes();

onMounted(() => {
  couponCodes.loadCouponCodes();
});
</script>

<template>
  <AdminCouponCodesPanel
    :state="couponCodes.state"
    @apply-filter="couponCodes.applyFilter"
    @change-page="couponCodes.changePage"
    @create="couponCodes.openCreate"
    @edit="couponCodes.openEdit"
    @toggle="couponCodes.toggleCoupon"
    @delete="couponCodes.removeCoupon"
    @update-keyword="couponCodes.state.keyword = $event"
    @update-status="couponCodes.state.status = $event"
  />
  <CouponCodeModal
    :open="couponCodes.modalOpen.value"
    :target="couponCodes.target.value"
    :saving="couponCodes.saving.value"
    @close="couponCodes.modalOpen.value = false"
    @submit="couponCodes.saveCoupon"
  />
</template>
