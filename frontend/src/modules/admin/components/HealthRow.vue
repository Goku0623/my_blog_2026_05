<template>
  <div class="flex items-center justify-between text-sm">
    <span class="text-[var(--text-soft)]">{{ label }}</span>
    <span class="inline-flex items-center gap-1.5">
      <span :class="['size-1.5 rounded-full', okCls]"></span>
      <span class="text-[var(--text)]">{{ status }}</span>
    </span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props { label: string; status: string }
const props = defineProps<Props>()

const okCls = computed(() => {
  const s = (props.status || '').toLowerCase()
  if (s.includes('connected') || s.includes('healthy') || s.includes('ok') || s.includes('running')) {
    return 'bg-emerald-500'
  }
  if (s.includes('checking')) return 'bg-amber-400 animate-pulse-soft'
  return 'bg-rose-500'
})
</script>
