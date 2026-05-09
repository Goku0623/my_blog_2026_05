<template>
  <footer class="relative mt-16 border-t border-[var(--border)] bg-[var(--bg-soft)]/60 backdrop-blur">
    <div class="relative container-page py-6 sm:py-8">
      <div class="flex flex-col gap-3 text-xs text-[var(--text-muted)] md:flex-row md:items-center md:justify-between">
        <p>&copy; {{ year }} {{ siteStore.config.site_name }} · All rights reserved.</p>
        <div class="flex flex-wrap items-center gap-x-4 gap-y-2">
          <span class="opacity-80">Made with Vue 3 + FastAPI</span>
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
import { computed } from 'vue'
import { useSiteStore } from '@/stores/site'

const siteStore = useSiteStore()
const year = computed(() => new Date().getFullYear())
</script>
