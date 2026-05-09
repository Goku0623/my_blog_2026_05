<template>
  <nav v-if="totalPages > 1" class="flex items-center justify-center gap-1.5">
    <button
      type="button"
      class="page-btn"
      :disabled="current <= 1"
      @click="go(current - 1)"
    >
      <ChevronLeft class="size-4" />
    </button>
    <button
      v-for="(p, idx) in visible"
      :key="idx"
      type="button"
      :class="['page-btn', typeof p === 'number' && p === current ? 'page-btn-active' : '']"
      :disabled="typeof p !== 'number'"
      @click="typeof p === 'number' && go(p)"
    >
      <span v-if="typeof p === 'number'">{{ p }}</span>
      <span v-else class="text-[var(--text-muted)]">…</span>
    </button>
    <button
      type="button"
      class="page-btn"
      :disabled="current >= totalPages"
      @click="go(current + 1)"
    >
      <ChevronRight class="size-4" />
    </button>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ChevronLeft, ChevronRight } from 'lucide-vue-next'

interface Props {
  current: number
  pageSize: number
  total: number
}

const props = defineProps<Props>()
const emit = defineEmits<{ (e: 'update:current', v: number): void; (e: 'change', v: number): void }>()

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)))

const visible = computed<(number | string)[]>(() => {
  const last = totalPages.value
  const cur = props.current
  if (last <= 7) return Array.from({ length: last }, (_, i) => i + 1)
  const list: (number | string)[] = [1]
  if (cur > 4) list.push('…')
  const start = Math.max(2, cur - 1)
  const end = Math.min(last - 1, cur + 1)
  for (let i = start; i <= end; i++) list.push(i)
  if (cur < last - 3) list.push('…')
  list.push(last)
  return list
})

const go = (page: number) => {
  if (page < 1 || page > totalPages.value || page === props.current) return
  emit('update:current', page)
  emit('change', page)
}
</script>

<style scoped>
.page-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 2.25rem;
  min-width: 2.25rem;
  padding: 0 0.5rem;
  border-radius: 0.5rem;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  font-size: 0.875rem;
  font-weight: 500;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
}
.page-btn:hover:not(:disabled) {
  background: var(--bg-muted);
}
.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.page-btn-active {
  background: var(--brand);
  border-color: var(--brand);
  color: var(--text-on-brand);
}
.page-btn-active:hover {
  background: var(--brand-strong);
  color: var(--text-on-brand);
}
</style>
