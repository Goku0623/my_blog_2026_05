<template>
  <span
    :class="[
      'inline-flex items-center gap-1 font-medium leading-none',
      sizeCls,
      variantCls,
      rounded ? 'rounded-full' : 'rounded-md',
      $attrs.onClick && 'cursor-pointer hover:opacity-80',
    ]"
  >
    <slot />
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  variant?: 'brand' | 'info' | 'success' | 'warning' | 'danger' | 'neutral' | 'outline'
  size?: 'sm' | 'md'
  rounded?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'neutral',
  size: 'sm',
  rounded: false,
})

defineOptions({ inheritAttrs: true })

const sizeCls = computed(() =>
  props.size === 'md' ? 'px-2.5 py-1 text-xs' : 'px-2 py-0.5 text-xs'
)

const variantCls = computed(() => {
  switch (props.variant) {
    case 'brand':
      return 'bg-[var(--brand-soft)] text-[var(--brand)]'
    case 'info':
      return 'bg-blue-50 text-blue-600 dark:bg-blue-950/40 dark:text-blue-300'
    case 'success':
      return 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-300'
    case 'warning':
      return 'bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-300'
    case 'danger':
      return 'bg-rose-50 text-rose-600 dark:bg-rose-950/40 dark:text-rose-300'
    case 'outline':
      return 'border border-[var(--border-strong)] text-[var(--text-soft)]'
    default:
      return 'bg-[var(--bg-muted)] text-[var(--text-soft)]'
  }
})
</script>
