import { readonly, ref } from "vue";

const open = ref(false);

export function useRechargeModal() {
  function openRechargeModal() {
    open.value = true;
  }

  function closeRechargeModal() {
    open.value = false;
  }

  return {
    rechargeModalOpen: readonly(open),
    openRechargeModal,
    closeRechargeModal,
  };
}
