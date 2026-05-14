<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="modelValue"
        class="fixed inset-0 z-[1000] flex items-center justify-center p-4"
        @mousedown.self="onMaskClick"
      >
        <div
          :class="[
            'absolute inset-0 bg-[var(--ink-950)]/40',
            backdropBlur ? 'backdrop-blur-sm' : '',
          ]"
          aria-hidden="true"
        ></div>
        <div
          :class="[
            'relative w-full bg-[var(--surface)] rounded-2xl shadow-[var(--shadow-lg)] border border-[var(--border)]',
            'max-h-[90vh] flex flex-col overflow-hidden',
            widthCls,
          ]"
          role="dialog"
          aria-modal="true"
        >
          <header v-if="title || $slots.header" class="flex items-center justify-between px-6 pt-5 pb-4 border-b border-[var(--border)]">
            <slot name="header">
              <h3 class="text-lg font-semibold text-[var(--text)]">{{ title }}</h3>
            </slot>
            <button
              v-if="closable"
              type="button"
              class="ml-4 rounded-md p-1.5 text-[var(--text-muted)] hover:bg-[var(--bg-muted)] hover:text-[var(--text)] transition-colors"
              @click="close"
              aria-label="关闭"
            >
              <X class="size-4" />
            </button>
          </header>
          <div class="flex-1 overflow-y-auto px-6 py-5">
            <slot />
          </div>
          <footer v-if="$slots.footer" class="px-6 py-4 border-t border-[var(--border)] bg-[var(--bg-soft)] flex justify-end gap-2">
            <slot name="footer" />
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { X } from 'lucide-vue-next'

interface Props {
  modelValue: boolean
  title?: string
  width?: 'sm' | 'md' | 'lg' | 'xl'
  closable?: boolean
  closeOnMask?: boolean
  backdropBlur?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  width: 'md',
  closable: true,
  closeOnMask: true,
  backdropBlur: true,
})

const emit = defineEmits<{ (e: 'update:modelValue', v: boolean): void }>()

const close = () => emit('update:modelValue', false)

const onMaskClick = () => {
  if (props.closeOnMask) close()
}

const widthCls = computed(() => {
  const map = { sm: 'max-w-sm', md: 'max-w-md', lg: 'max-w-2xl', xl: 'max-w-4xl' }
  return map[props.width]
})

watch(
  () => props.modelValue,
  (val) => {
    if (typeof document === 'undefined') return
    document.documentElement.style.overflow = val ? 'hidden' : ''
  }
)
</script>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}
.modal-enter-active > div:last-child,
.modal-leave-active > div:last-child {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
.modal-enter-from > div:last-child,
.modal-leave-to > div:last-child {
  transform: translateY(8px) scale(0.98);
  opacity: 0;
}
</style>
