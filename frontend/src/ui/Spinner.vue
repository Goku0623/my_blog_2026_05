<template>
  <span
    class="inline-block animate-spin rounded-full border-2 border-current border-r-transparent"
    :style="{ width: `${size}px`, height: `${size}px`, color }"
    role="status"
    aria-label="loading"
  />
</template>

<script setup lang="ts">
interface Props {
  size?: number
  color?: string
}
withDefaults(defineProps<Props>(), { size: 16, color: 'currentColor' })
</script>
