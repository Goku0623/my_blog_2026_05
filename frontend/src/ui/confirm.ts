import { h, render, type App } from 'vue'
import Confirm from './Confirm.vue'

interface ConfirmOptions {
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  danger?: boolean
}

let confirmInstance: any = null

const ensureInstance = () => {
  if (confirmInstance) return confirmInstance
  const container = document.createElement('div')
  document.body.appendChild(container)
  const vnode = h(Confirm)
  if ((window as any).__cursorConfirmApp) {
    vnode.appContext = (window as any).__cursorConfirmApp._context
  }
  render(vnode, container)
  confirmInstance = vnode.component?.exposed
  return confirmInstance
}

export const confirmDialog = (options: ConfirmOptions) => {
  const instance = ensureInstance()
  return instance.open(options) as Promise<boolean>
}

export const installConfirm = (app: App) => {
  ;(window as any).__cursorConfirmApp = app
}
