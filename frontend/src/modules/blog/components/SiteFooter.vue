<template>
  <footer class="relative mt-16 border-t border-[var(--border)] bg-[var(--bg-soft)]/60 backdrop-blur">
    <!-- 大字背景 -->
    <div
      aria-hidden="true"
      class="pointer-events-none select-none absolute inset-x-0 -top-2 overflow-hidden text-center"
    >
      <p class="hero-headline text-[18vw] sm:text-[14vw] lg:text-[10rem] leading-none whitespace-nowrap bg-gradient-to-b from-[var(--text)]/[0.06] to-transparent bg-clip-text text-transparent">
        {{ siteStore.config.site_name }}
      </p>
    </div>

    <div class="relative container-page pt-14 pb-10 sm:pt-20 sm:pb-12">
      <div class="grid gap-10 md:grid-cols-12">
        <div class="md:col-span-5">
          <router-link to="/" class="inline-flex items-center gap-3">
            <span class="grid place-items-center size-10 rounded-xl bg-gradient-to-br from-[var(--brand)] via-[#9333ea] to-[var(--accent)] text-white font-bold shadow-[var(--shadow-md)]">
              {{ initialChar }}
            </span>
            <span class="text-lg font-semibold tracking-tight text-[var(--text)]">
              {{ siteStore.config.site_name }}
            </span>
          </router-link>
          <p class="mt-4 max-w-md text-sm leading-relaxed text-[var(--text-soft)]">
            {{ siteStore.config.site_description || '记录技术、生活与思考，专注 Web 开发、AI 应用与开源探索。' }}
          </p>
        </div>

        <div class="md:col-span-3">
          <p class="text-xs font-semibold tracking-[0.2em] uppercase text-[var(--text-muted)]">导航</p>
          <ul class="mt-4 space-y-2.5 text-sm">
            <li>
              <router-link to="/" class="text-[var(--text-soft)] hover:text-[var(--brand)] transition-colors">首页</router-link>
            </li>
            <li>
              <router-link to="/search" class="text-[var(--text-soft)] hover:text-[var(--brand)] transition-colors">探索文章</router-link>
            </li>
            <li>
              <router-link to="/admin" class="text-[var(--text-soft)] hover:text-[var(--brand)] transition-colors">后台管理</router-link>
            </li>
          </ul>
        </div>

        <div class="md:col-span-4">
          <p class="text-xs font-semibold tracking-[0.2em] uppercase text-[var(--text-muted)]">关于</p>
          <p class="mt-4 text-sm leading-relaxed text-[var(--text-soft)]">
            一站基于
            <span class="font-medium text-[var(--text)]">FastAPI</span>
            +
            <span class="font-medium text-[var(--text)]">Vue 3</span>
            构建的现代化博客系统，注重内容、性能与体验。
          </p>
          <div class="mt-4 flex items-center gap-2">
            <a
              href="#"
              aria-label="GitHub"
              class="size-9 grid place-items-center rounded-full border border-[var(--border)] text-[var(--text-soft)] hover:text-[var(--brand)] hover:border-[var(--brand)] transition-colors"
              @click.prevent
            >
              <Github class="size-4" />
            </a>
            <a
              href="#"
              aria-label="Twitter"
              class="size-9 grid place-items-center rounded-full border border-[var(--border)] text-[var(--text-soft)] hover:text-[var(--brand)] hover:border-[var(--brand)] transition-colors"
              @click.prevent
            >
              <Twitter class="size-4" />
            </a>
            <a
              href="#"
              aria-label="Mail"
              class="size-9 grid place-items-center rounded-full border border-[var(--border)] text-[var(--text-soft)] hover:text-[var(--brand)] hover:border-[var(--brand)] transition-colors"
              @click.prevent
            >
              <Mail class="size-4" />
            </a>
            <a
              href="#"
              aria-label="RSS"
              class="size-9 grid place-items-center rounded-full border border-[var(--border)] text-[var(--text-soft)] hover:text-[var(--brand)] hover:border-[var(--brand)] transition-colors"
              @click.prevent
            >
              <Rss class="size-4" />
            </a>
          </div>
        </div>
      </div>

      <div class="mt-10 hairline-divider"></div>

      <div class="mt-6 flex flex-col gap-3 text-xs text-[var(--text-muted)] md:flex-row md:items-center md:justify-between">
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
import { Github, Twitter, Mail, Rss } from 'lucide-vue-next'

const siteStore = useSiteStore()
const year = computed(() => new Date().getFullYear())
const initialChar = computed(() => Array.from(siteStore.config.site_name || 'B')[0]?.toUpperCase() ?? 'B')
</script>
