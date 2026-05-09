<template>
  <component
    :is="tag"
    :type="tag === 'button' ? type : undefined"
    :disabled="loading || disabled"
    :class="[
      'inline-flex items-center justify-center gap-2 font-medium select-none',
      'transition-[background,box-shadow,color,border-color,transform] duration-150 active:scale-[0.98]',
      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand)]/40',
      'disabled:cursor-not-allowed disabled:opacity-60 disabled:active:scale-100',
      sizeCls,
      variantCls,
      block && 'w-full',
    ]"
  >
    <span
      v-if="loading"
      class="inline-block size-3.5 animate-spin rounded-full border-2 border-current border-r-transparent"
    />
    <slot v-else name="icon" />
    <slot />
  </component>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  variant?: 'primary' | 'secondary' | 'ghost' | 'outline' | 'danger' | 'subtle'
  size?: 'sm' | 'md' | 'lg' | 'icon'
  type?: 'button' | 'submit' | 'reset'
  tag?: string
  disabled?: boolean
  loading?: boolean
  block?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  type: 'button',
  tag: 'button',
  disabled: false,
  loading: false,
  block: false,
})

const sizeCls = computed(() => {
  switch (props.size) {
    case 'sm':
      return 'h-8 px-3 text-sm rounded-lg'
    case 'lg':
      return 'h-12 px-6 text-base rounded-xl'
    case 'icon':
      return 'size-9 rounded-lg'
    default:
      return 'h-10 px-4 text-sm rounded-lg'
  }
})

const variantCls = computed(() => {
  switch (props.variant) {
    case 'primary':
      return 'bg-[var(--brand)] text-[var(--text-on-brand)] shadow-sm hover:shadow-md hover:bg-[var(--brand-strong)]'
    case 'secondary':
      return 'bg-[var(--bg-muted)] text-[var(--text)] hover:bg-[var(--border)]'
    case 'ghost':
      return 'bg-transparent text-[var(--text-soft)] hover:bg-[var(--bg-muted)] hover:text-[var(--text)]'
    case 'outline':
      return 'bg-transparent border border-[var(--border-strong)] text-[var(--text)] hover:bg-[var(--bg-muted)]'
    case 'danger':
      return 'bg-[var(--danger)] text-white hover:opacity-90'
    case 'subtle':
      return 'bg-[var(--brand-soft)] text-[var(--brand)] hover:bg-[var(--brand)]/10'
    default:
      return ''
  }
})
</script>
