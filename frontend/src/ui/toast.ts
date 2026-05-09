import { reactive } from 'vue'

export type ToastVariant = 'success' | 'error' | 'warning' | 'info'

export interface ToastItem {
  id: number
  message: string
  variant: ToastVariant
  duration: number
}

let nextId = 1
export const toastState = reactive<{ items: ToastItem[] }>({ items: [] })

const dismiss = (id: number) => {
  const idx = toastState.items.findIndex((it) => it.id === id)
  if (idx >= 0) toastState.items.splice(idx, 1)
}

const push = (variant: ToastVariant, message: string, duration = 3000) => {
  const id = nextId++
  toastState.items.push({ id, message, variant, duration })
  if (duration > 0) {
    window.setTimeout(() => dismiss(id), duration)
  }
  return id
}

export const toast = {
  success: (msg: string, duration?: number) => push('success', msg, duration),
  error: (msg: string, duration?: number) => push('error', msg, duration),
  warning: (msg: string, duration?: number) => push('warning', msg, duration),
  info: (msg: string, duration?: number) => push('info', msg, duration),
  dismiss,
}
