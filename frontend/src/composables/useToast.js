import { reactive } from 'vue'

const toasts = reactive([])

export function useToast() {
  function push(type, message) {
    const id = `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
    toasts.push({ id, type, message })
    window.setTimeout(() => remove(id), 2800)
  }

  function remove(id) {
    const index = toasts.findIndex((toast) => toast.id === id)
    if (index > -1) {
      toasts.splice(index, 1)
    }
  }

  return {
    toasts,
    success: (message) => push('success', message),
    error: (message) => push('error', message),
    info: (message) => push('info', message),
    remove,
  }
}
