<template>
  <Modal v-model="visible" :title="opts.title" width="sm" :closable="!opts.loading">
    <p class="text-sm text-[var(--text-soft)] leading-relaxed">{{ opts.message }}</p>
    <template #footer>
      <Button variant="ghost" :disabled="opts.loading" @click="onCancel">{{ opts.cancelText }}</Button>
      <Button :variant="opts.danger ? 'danger' : 'primary'" :loading="opts.loading" @click="onConfirm">{{ opts.confirmText }}</Button>
    </template>
  </Modal>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import Modal from './Modal.vue'
import Button from './Button.vue'

interface ConfirmOptions {
  title: string
  message: string
  confirmText: string
  cancelText: string
  danger: boolean
  loading: boolean
}

const visible = ref(false)
const opts = reactive<ConfirmOptions>({
  title: '提示',
  message: '',
  confirmText: '确认',
  cancelText: '取消',
  danger: false,
  loading: false,
})

let resolver: ((v: boolean) => void) | null = null

const open = (options: Partial<Omit<ConfirmOptions, 'loading'>>) => {
  Object.assign(opts, {
    title: '提示',
    message: '',
    confirmText: '确认',
    cancelText: '取消',
    danger: false,
    loading: false,
    ...options,
  })
  visible.value = true
  return new Promise<boolean>((resolve) => {
    resolver = resolve
  })
}

const close = (val: boolean) => {
  if (resolver) {
    resolver(val)
    resolver = null
  }
  visible.value = false
}

const onCancel = () => close(false)
const onConfirm = () => close(true)

defineExpose({ open })
</script>
