<template>
  <div class="min-h-screen flex flex-col bg-[var(--bg)]">
    <SiteNavbar />

    <!-- Hero -->
    <section class="relative overflow-hidden">
      <div aria-hidden="true" class="hero-orb size-[420px] -top-32 left-1/2 -translate-x-1/2 bg-[var(--brand)]/15"></div>

      <div class="container-page relative pt-12 sm:pt-16 pb-10">
        <div class="text-center max-w-3xl mx-auto">
          <span class="eyebrow"><User class="size-3" /> About</span>
          <h1 class="mt-3 hero-headline text-[clamp(2rem,5vw,3.75rem)] text-[var(--text)] leading-[1.1]">
            关于<span class="text-gradient-brand">我</span>
          </h1>
          <p class="mt-4 text-base text-[var(--text-soft)]">
            了解更多关于博主和本站的信息
          </p>
        </div>
      </div>
    </section>

    <!-- 内容 -->
    <main class="flex-1 pb-16 sm:pb-20">
      <div class="container-page">
        <div class="mx-auto max-w-3xl">
          <!-- 博主信息卡 -->
          <div class="relative overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 sm:p-8 shadow-[var(--shadow-sm)]">
            <div aria-hidden="true" class="absolute -top-12 -right-12 size-32 bg-[var(--brand)]/15 rounded-full blur-2xl"></div>

            <div class="relative flex flex-col sm:flex-row items-center sm:items-start gap-6">
              <div class="grid place-items-center size-20 sm:size-24 rounded-2xl bg-gradient-to-br from-[var(--brand)] via-[#9333ea] to-[var(--accent)] text-white font-bold text-3xl shadow-[var(--shadow-md)] shrink-0">
                {{ initialChar }}
              </div>
              <div class="text-center sm:text-left flex-1">
                <h2 class="font-display text-xl sm:text-2xl font-bold text-[var(--text)]">
                  {{ siteStore.config.site_author || '博主' }}
                </h2>
                <p class="mt-1 text-sm text-[var(--text-muted)]">
                  {{ siteStore.config.site_name }}
                </p>
                <p class="mt-3 text-sm leading-relaxed text-[var(--text-soft)]">
                  {{ siteStore.config.site_description || '记录技术、生活与思考，专注 Web 开发、AI 应用与开源探索。' }}
                </p>
              </div>
            </div>

            <!-- 社交链接 -->
            <div class="mt-6 pt-6 border-t border-[var(--border)] flex flex-wrap items-center justify-center sm:justify-start gap-3">
              <a
                href="#"
                aria-label="GitHub"
                class="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-[var(--border)] text-sm text-[var(--text-soft)] hover:text-[var(--brand)] hover:border-[var(--brand)] transition-colors"
                @click.prevent
              >
                <Github class="size-4" /> GitHub
              </a>
              <a
                href="#"
                aria-label="Email"
                class="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-[var(--border)] text-sm text-[var(--text-soft)] hover:text-[var(--brand)] hover:border-[var(--brand)] transition-colors"
                @click.prevent
              >
                <Mail class="size-4" /> 邮箱
              </a>
              <a
                href="#"
                aria-label="Twitter"
                class="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-[var(--border)] text-sm text-[var(--text-soft)] hover:text-[var(--brand)] hover:border-[var(--brand)] transition-colors"
                @click.prevent
              >
                <Twitter class="size-4" /> Twitter
              </a>
            </div>
          </div>

          <!-- 站点信息 -->
          <div class="mt-8 rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 sm:p-8 shadow-[var(--shadow-sm)]">
            <h3 class="font-display text-lg font-semibold text-[var(--text)] mb-4">关于本站</h3>
            <div class="space-y-4 text-sm text-[var(--text-soft)] leading-relaxed">
              <p>
                这是一个基于 <span class="font-medium text-[var(--text)]">FastAPI</span> + <span class="font-medium text-[var(--text)]">Vue 3</span> 构建的现代化个人博客系统。
              </p>
              <p>
                本站采用前后端分离架构，注重内容展示、性能优化与用户体验。设计风格偏向现代杂志风，支持亮色/暗色主题切换，文章支持 Markdown 渲染与代码高亮。
              </p>
              <p>
                如果你对本站的技术实现感兴趣，欢迎通过上方链接与博主交流。
              </p>
            </div>

          </div>
        </div>
      </div>
    </main>

    <SiteFooter />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { User, Github, Mail, Twitter } from 'lucide-vue-next'
import { useSiteStore } from '@/stores/site'
import SiteNavbar from '../components/SiteNavbar.vue'
import SiteFooter from '../components/SiteFooter.vue'

const siteStore = useSiteStore()

const initialChar = computed(() => Array.from(siteStore.config.site_name || 'B')[0]?.toUpperCase() ?? 'B')
</script>