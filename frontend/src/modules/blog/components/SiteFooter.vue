<template>
  <footer class="relative mt-16 border-t border-[var(--border)] bg-[var(--bg-soft)]/60 backdrop-blur">
    <div class="relative container-page py-6 sm:py-8">
      <div class="flex flex-col gap-3 text-xs text-[var(--text-muted)] md:flex-row md:items-center md:justify-between">
        <p>&copy; {{ year }} {{ siteStore.config.site_name }} · All rights reserved.</p>
        <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
          <span v-if="uptimeText" class="inline-block tabular-nums transform-gpu will-change-[contents]" aria-live="polite">{{ uptimeText }}</span>
          <a
            v-if="siteStore.config.icp_number"
            href="https://beian.miit.gov.cn/"
            target="_blank"
            rel="noopener noreferrer"
            class="hover:text-[var(--brand)] transition-colors"
          >{{ siteStore.config.icp_number }}</a>
        </div>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { computed, ref, watch, onBeforeUnmount } from 'vue'
import { useSiteStore } from '@/stores/site'

const siteStore = useSiteStore()
const year = computed(() => new Date().getFullYear())

const elapsed = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const startedAt = computed(() => {
  const raw = siteStore.config.site_started_at
  if (!raw) return null
  const d = new Date(raw)
  return isNaN(d.getTime()) ? null : d
})

const uptimeText = computed(() => {
  if (!startedAt.value) return null
  const totalSeconds = Math.max(0, Math.floor(elapsed.value))
  const days = Math.floor(totalSeconds / 86400)
  const hours = Math.floor((totalSeconds % 86400) / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  return `本站已正式上线运行${days}天${hours}小时${minutes}分钟${seconds}秒`
})

const startTimer = () => {
  if (timer !== null) return
  if (!startedAt.value) return
  const startTime = startedAt.value.getTime()
  elapsed.value = (Date.now() - startTime) / 1000
  timer = setInterval(() => {
    elapsed.value = (Date.now() - startTime) / 1000
  }, 1000)
}

const stopTimer = () => {
  if (timer !== null) {
    clearInterval(timer)
    timer = null
  }
}

watch(startedAt, (v) => {
  stopTimer()
  if (v) startTimer()
}, { immediate: true })

onBeforeUnmount(() => {
  stopTimer()
})
</script>
