import { reactive } from 'vue'

const state = reactive({
  open: false,
  title: '',
  message: '',
  confirmText: '确认',
  cancelText: '取消',
  tone: 'default', // 'default' | 'danger'
  resolve: null,
})

export function useConfirm() {
  function open({ title = '确认', message = '', confirmText = '确认', cancelText = '取消', tone = 'default' } = {}) {
    return new Promise((resolve) => {
      // 如果已经有一个打开的确认框，先关闭它（resolve false）
      if (state.open && state.resolve) {
        state.resolve(false)
      }
      state.title = title
      state.message = message
      state.confirmText = confirmText
      state.cancelText = cancelText
      state.tone = tone
      state.resolve = resolve
      state.open = true
    })
  }

  function confirm() {
    state.open = false
    state.resolve?.(true)
    state.resolve = null
  }

  function cancel() {
    state.open = false
    state.resolve?.(false)
    state.resolve = null
  }

  return {
    state,
    open,
    confirm,
    cancel,
  }
}
