<template>
  <Teleport to="body">
    <div class="fixed top-4 right-4 z-[2000] flex flex-col items-end gap-2 pointer-events-none">
      <TransitionGroup name="toast" tag="div" class="flex flex-col gap-2 items-end">
        <div
          v-for="t in toastState.items"
          :key="t.id"
          :class="[
            'pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-xl border shadow-[var(--shadow-md)] min-w-[260px] max-w-[420px]',
            'bg-[var(--surface)] backdrop-blur',
            variantCls(t.variant),
          ]"
        >
          <component :is="iconOf(t.variant)" class="size-5 mt-0.5 shrink-0" />
          <p class="flex-1 text-sm leading-snug text-[var(--text)]">{{ t.message }}</p>
          <button
            class="text-[var(--text-muted)] hover:text-[var(--text)] -mt-0.5"
            @click="toast.dismiss(t.id)"
            aria-label="关闭"
          >
            <X class="size-4" />
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { CheckCircle2, AlertTriangle, AlertCircle, Info, X } from 'lucide-vue-next'
import { toast, toastState, type ToastVariant } from './toast'

const variantCls = (v: ToastVariant) => {
  switch (v) {
    case 'success':
      return 'border-emerald-200 dark:border-emerald-700/40 [&_svg]:text-emerald-500'
    case 'error':
      return 'border-rose-200 dark:border-rose-700/40 [&_svg]:text-rose-500'
    case 'warning':
      return 'border-amber-200 dark:border-amber-700/40 [&_svg]:text-amber-500'
    default:
      return 'border-blue-200 dark:border-blue-700/40 [&_svg]:text-blue-500'
  }
}
const iconOf = (v: ToastVariant) => {
  switch (v) {
    case 'success':
      return CheckCircle2
    case 'error':
      return AlertCircle
    case 'warning':
      return AlertTriangle
    default:
      return Info
  }
}
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: transform 0.25s ease, opacity 0.25s ease;
}
.toast-enter-from {
  transform: translateX(20px);
  opacity: 0;
}
.toast-leave-to {
  transform: translateX(20px);
  opacity: 0;
}
</style>
