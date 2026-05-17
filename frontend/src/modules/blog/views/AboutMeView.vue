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
              <div class="grid place-items-center size-20 sm:size-24 rounded-2xl bg-gradient-to-br from-[var(--brand)] via-[#9333ea] to-[var(--accent)] text-white font-bold text-3xl shadow-[var(--shadow-md)] shrink-0 overflow-hidden">
                <img v-if="siteStore.config.admin_avatar" :src="siteStore.config.admin_avatar" alt="" class="size-full object-cover" />
                <span v-else>{{ initialChar }}</span>
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
                v-if="siteStore.config.github_url"
                :href="siteStore.config.github_url"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="GitHub"
                class="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-[var(--border)] text-sm text-[var(--text-soft)] hover:text-[var(--brand)] hover:border-[var(--brand)] transition-colors"
              >
                <Github class="size-4" /> GitHub
              </a>
              <a
                v-if="siteStore.config.bilibili_url"
                :href="siteStore.config.bilibili_url"
                target="_blank"
                rel="noopener noreferrer"
                aria-label="Bilibili"
                class="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-[var(--border)] text-sm text-[var(--text-soft)] hover:text-[var(--brand)] hover:border-[var(--brand)] transition-colors"
              >
                <svg class="size-4" viewBox="0 0 24 24" fill="currentColor"><path d="M17.813 4.653h.854c1.51.054 2.769.578 3.773 1.574 1.004.995 1.524 2.249 1.56 3.76v7.36c-.036 1.51-.556 2.769-1.56 3.773s-2.262 1.524-3.773 1.56H5.333c-1.51-.036-2.769-.556-3.773-1.56S.036 18.858 0 17.347v-7.36c.036-1.511.556-2.765 1.56-3.76 1.004-.996 2.262-1.52 3.773-1.574h.774l-1.174-1.12a1.234 1.234 0 0 1-.373-.906c0-.356.124-.658.373-.907l.027-.027c.267-.249.573-.373.92-.373.347 0 .653.124.92.373L9.653 4.44c.071.071.134.142.187.213h4.267a.836.836 0 0 1 .16-.213l2.853-2.747c.267-.249.573-.373.92-.373.347 0 .662.151.929.4.267.249.391.551.391.907 0 .355-.124.657-.373.906zM5.333 7.24c-.746.018-1.373.276-1.88.773-.506.498-.769 1.13-.786 1.894v7.52c.017.764.28 1.395.786 1.893.507.498 1.134.756 1.88.773h13.334c.746-.017 1.373-.275 1.88-.773.506-.498.769-1.129.786-1.893v-7.52c-.017-.765-.28-1.396-.786-1.894-.507-.497-1.134-.755-1.88-.773zM8 11.107c.373 0 .684.124.933.373.25.249.383.569.4.96v1.173c-.017.391-.15.711-.4.96-.249.25-.56.374-.933.374s-.684-.125-.933-.374c-.25-.249-.383-.569-.4-.96V12.44c0-.373.129-.689.386-.947.258-.257.574-.386.947-.386zm8 0c.373 0 .684.124.933.373.25.249.383.569.4.96v1.173c-.017.391-.15.711-.4.96-.249.25-.56.374-.933.374s-.684-.125-.933-.374c-.25-.249-.383-.569-.4-.96V12.44c.017-.391.15-.711.4-.96.249-.249.56-.373.933-.373z"/></svg>
                Bilibili
              </a>
              <button
                type="button"
                class="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-[var(--border)] text-sm text-[var(--text-soft)] hover:text-[var(--brand)] hover:border-[var(--brand)] transition-colors"
                @click="openEmailModal"
              >
                <Mail class="size-4" /> Email
              </button>
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

    <!-- 邮箱弹窗 -->
    <Teleport to="body">
      <transition
        enter-active-class="transition duration-150 ease-[cubic-bezier(0.2,0.8,0.2,1)]"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition duration-100 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-show="emailModalVisible"
          class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/38 cursor-pointer transform-gpu will-change-[opacity] motion-reduce:transition-none"
          @click.self="emailModalVisible = false"
        >
          <div
            class="relative w-full max-w-sm rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-[var(--shadow-xl)] transform-gpu will-change-transform cursor-auto [contain:layout_style]"
            :class="emailModalVisible ? 'animate-email-in' : ''"
          >
            <div class="text-center">
              <div class="grid place-items-center size-12 mx-auto rounded-full bg-[var(--brand-soft)]">
                <Mail class="size-5 text-[var(--brand)]" />
              </div>
              <h3 class="mt-4 font-display text-lg font-semibold text-[var(--text)]">联系邮箱</h3>
              <p class="mt-1 text-sm text-[var(--text-muted)]">欢迎通过邮件与博主取得联系</p>
              <div class="mt-4 flex items-center gap-2 rounded-xl border border-[var(--border)] bg-[var(--bg-soft)] px-4 py-3">
                <span class="flex-1 text-sm font-mono text-[var(--text)] break-all text-left">{{ emailToShow }}</span>
                <button
                  type="button"
                  class="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all active:scale-95"
                  :class="copied ? 'bg-emerald-500/15 text-emerald-500' : 'bg-[var(--brand)] text-white hover:opacity-90'"
                  @click="copyEmail"
                >
                  <Check v-if="copied" class="size-3.5" />
                  <Copy v-else class="size-3.5" />
                  {{ copied ? '已复制' : '复制' }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { User, Github, Mail, Copy, Check } from 'lucide-vue-next'
import { useSiteStore } from '@/stores/site'
import { toast } from '@/ui'
import SiteNavbar from '../components/SiteNavbar.vue'
import SiteFooter from '../components/SiteFooter.vue'

const siteStore = useSiteStore()

const initialChar = computed(() => Array.from(siteStore.config.site_name || 'B')[0]?.toUpperCase() ?? 'B')

const emailModalVisible = ref(false)
const copied = ref(false)
let copyTimer: ReturnType<typeof setTimeout> | null = null

const emailToShow = computed(() => siteStore.config.admin_email || 'admin@example.com')

const openEmailModal = () => {
  copied.value = false
  if (copyTimer) { clearTimeout(copyTimer); copyTimer = null }
  emailModalVisible.value = true
}

const copyEmail = async () => {
  try {
    await navigator.clipboard.writeText(emailToShow.value)
    copied.value = true
    toast.success('邮箱已复制到剪贴板')
    if (copyTimer) clearTimeout(copyTimer)
    copyTimer = setTimeout(() => {
      copied.value = false
      copyTimer = null
    }, 2000)
  } catch {
    toast.error('复制失败，请手动复制')
  }
}
</script>

<style scoped>
@keyframes email-in {
  from {
    opacity: 0;
    transform: scale(0.96) translateY(6px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
.animate-email-in {
  animation: email-in 0.18s cubic-bezier(0.2, 0.8, 0.2, 1) both;
}
</style>