<template>
  <span
    :class="[
      'inline-flex items-center justify-center font-semibold text-white shrink-0 select-none',
      shape === 'circle' ? 'rounded-full' : 'rounded-md',
      sizeCls,
    ]"
    :style="bgStyle"
  >
    <img v-if="src" :src="src" :alt="alt" class="size-full rounded-[inherit] object-cover" />
    <slot v-else>{{ defaultLetter }}</slot>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  src?: string
  alt?: string
  name?: string
  size?: number
  shape?: 'circle' | 'square'
  color?: string
}

const props = withDefaults(defineProps<Props>(), {
  size: 36,
  shape: 'circle',
})

const PALETTE = [
  '#f97316', '#a855f7', '#0ea5e9', '#10b981', '#f43f5e',
  '#3b82f6', '#facc15', '#06b6d4', '#ec4899', '#84cc16',
]

const defaultLetter = computed(() => {
  if (!props.name) return ''
  return Array.from(props.name)[0]?.toUpperCase() ?? ''
})

const bgStyle = computed(() => {
  if (props.color) return { backgroundColor: props.color, width: `${props.size}px`, height: `${props.size}px`, fontSize: `${Math.max(props.size / 2.5, 12)}px` }
  const seed = props.name?.charCodeAt(0) ?? 0
  return {
    backgroundColor: PALETTE[seed % PALETTE.length],
    width: `${props.size}px`,
    height: `${props.size}px`,
    fontSize: `${Math.max(props.size / 2.5, 12)}px`,
  }
})

const sizeCls = computed(() => '')
</script>
