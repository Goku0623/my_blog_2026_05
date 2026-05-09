<template>
  <div class="flex flex-col items-center justify-center py-16 text-[var(--text-muted)]">
    <slot name="icon">
      <Inbox class="size-12 mb-3 opacity-60" />
    </slot>
    <p class="text-sm">{{ description }}</p>
    <div v-if="$slots.default" class="mt-4">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Inbox } from 'lucide-vue-next'
withDefaults(defineProps<{ description?: string }>(), { description: '暂无数据' })
</script>
