<template>
  <div
    :class="[
      'animate-pulse-soft bg-[var(--bg-muted)]',
      rounded ? 'rounded-full' : 'rounded-md',
    ]"
    :style="{ width, height }"
  />
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{ width?: string; height?: string; rounded?: boolean }>(),
  { width: '100%', height: '14px', rounded: false }
)
</script>
