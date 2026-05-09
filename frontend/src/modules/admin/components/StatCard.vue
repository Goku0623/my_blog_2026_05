<template>
  <div class="surface-card p-5 flex items-center gap-4">
    <div :class="['grid place-items-center size-12 rounded-xl', bgCls]">
      <component :is="icon" :class="['size-5', textCls]" />
    </div>
    <div class="flex-1 min-w-0">
      <p class="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wide">{{ label }}</p>
      <p class="text-2xl font-semibold text-[var(--text)] mt-0.5">{{ formattedValue }}</p>
      <div v-if="$slots.extra" class="mt-1.5"><slot name="extra" /></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, type Component } from 'vue'

interface Props {
  label: string
  value: number | string
  icon: Component
  color?: 'blue' | 'green' | 'orange' | 'purple' | 'pink' | 'red'
}

const props = withDefaults(defineProps<Props>(), { color: 'blue' })

const formattedValue = computed(() => {
  if (typeof props.value !== 'number') return props.value
  if (props.value >= 10000) return `${(props.value / 10000).toFixed(1)}w`
  return props.value.toLocaleString()
})

const palette = {
  blue: { bg: 'bg-blue-50 dark:bg-blue-950/40', text: 'text-blue-500' },
  green: { bg: 'bg-emerald-50 dark:bg-emerald-950/40', text: 'text-emerald-500' },
  orange: { bg: 'bg-amber-50 dark:bg-amber-950/40', text: 'text-amber-500' },
  purple: { bg: 'bg-purple-50 dark:bg-purple-950/40', text: 'text-purple-500' },
  pink: { bg: 'bg-pink-50 dark:bg-pink-950/40', text: 'text-pink-500' },
  red: { bg: 'bg-rose-50 dark:bg-rose-950/40', text: 'text-rose-500' },
}

const bgCls = computed(() => palette[props.color].bg)
const textCls = computed(() => palette[props.color].text)
</script>
