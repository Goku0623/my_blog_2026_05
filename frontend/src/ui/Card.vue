<template>
  <div
    :class="[
      'surface-card overflow-hidden transition-shadow',
      hoverable && 'hover:shadow-[var(--shadow-md)] cursor-pointer',
      paddingCls,
    ]"
  >
    <header v-if="$slots.header" class="px-5 pt-4 pb-3 border-b border-[var(--border)]">
      <slot name="header" />
    </header>
    <div v-if="$slots.default" :class="bodyCls">
      <slot />
    </div>
    <footer v-if="$slots.footer" class="px-5 py-3 border-t border-[var(--border)] bg-[var(--bg-soft)]">
      <slot name="footer" />
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  hoverable?: boolean
  bodyClass?: string
  padding?: 'none' | 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<Props>(), {
  hoverable: false,
  padding: 'md',
})

const paddingCls = computed(() => '')

const bodyCls = computed(() => {
  const map = { none: '', sm: 'p-3', md: 'p-5', lg: 'p-6' }
  return [map[props.padding], props.bodyClass].filter(Boolean).join(' ')
})
</script>
