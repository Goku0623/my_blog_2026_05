<template>
  <div class="min-h-screen flex flex-col bg-[var(--bg)]">
    <!-- 阅读进度条 -->
    <div class="reading-progress" aria-hidden="true">
      <i :style="{ '--progress': progressPercent + '%' }"></i>
    </div>

    <SiteNavbar />

    <!-- 加载中 -->
    <div v-if="loading" class="container-page py-16">
      <USkeleton height="60px" class="rounded-xl mb-6 max-w-3xl" />
      <USkeleton height="320px" class="rounded-2xl" />
    </div>

    <!-- 详情 -->
    <article v-else-if="article" class="flex-1 animate-fade-in">
      <!-- ============================================================
           Article Hero
           ============================================================ -->
      <header class="relative overflow-hidden">
        <div aria-hidden="true" class="hero-orb size-[480px] -top-40 -left-32 bg-[var(--brand)]/20"></div>
        <div aria-hidden="true" class="hero-orb size-[360px] top-0 right-[-100px] bg-[var(--accent)]/20"></div>

        <div class="container-page relative pt-10 sm:pt-14 lg:pt-16 pb-10 sm:pb-12">
          <div class="max-w-3xl">
            <div class="flex flex-wrap items-center gap-3 text-xs text-[var(--text-muted)] mb-5">
              <router-link
                v-if="article.category"
                :to="`/category/${article.category.id}`"
                class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[var(--brand-soft)] text-[var(--brand)] font-medium hover:opacity-80 transition-opacity"
              >
                <Folder class="size-3" />
                {{ article.category.name }}
              </router-link>
              <span class="inline-flex items-center gap-1.5">
                <Calendar class="size-3" /> {{ formatFriendlyTime(article.created_at) }}
              </span>
              <span class="inline-flex items-center gap-1.5">
                <Eye class="size-3" /> {{ article.view_count }} 阅读
              </span>
              <span class="inline-flex items-center gap-1.5">
                <Clock class="size-3" /> {{ readingTime }} 分钟阅读
              </span>
            </div>

            <h1 class="hero-headline text-[clamp(2rem,5vw,4rem)] leading-[1.1] text-[var(--text)]">
              {{ article.title }}
            </h1>

            <p
              v-if="article.summary"
              class="mt-6 text-base sm:text-lg leading-relaxed text-[var(--text-soft)] border-l-2 border-[var(--brand)]/60 pl-4"
            >
              {{ article.summary }}
            </p>

            <div class="mt-8 flex items-center gap-4">
              <div class="grid place-items-center size-11 rounded-full bg-gradient-to-br from-[var(--brand)] to-[var(--accent)] text-white font-semibold shadow-[var(--shadow-md)]">
                {{ authorInitial }}
              </div>
              <div>
                <p class="text-sm font-medium text-[var(--text)]">{{ siteStore.config.site_author || '作者' }}</p>
                <p class="text-xs text-[var(--text-muted)]">{{ siteStore.config.site_name }}</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <!-- ============================================================
           Cover image
           ============================================================ -->
      <div v-if="article.cover_image" class="container-wide -mt-2 mb-8 sm:mb-12">
        <div class="relative overflow-hidden rounded-3xl border border-[var(--border)] shadow-[var(--shadow-xl)]">
          <img
            :src="article.cover_image"
            :alt="article.title"
            class="w-full max-h-[520px] object-cover"
          />
        </div>
      </div>

      <!-- ============================================================
           Body：正文 + 侧栏
           ============================================================ -->
      <div class="container-page pb-16">
        <div class="grid gap-10 xl:grid-cols-[minmax(0,1fr)_260px] xl:gap-14">
          <!-- 正文 -->
          <div ref="articleBody" class="min-w-0">
            <div
              class="prose prose-slate max-w-none dark:prose-invert prose-pre:rounded-xl prose-img:rounded-xl prose-headings:scroll-mt-24"
              v-html="renderedContent"
            />

            <!-- 标签条 -->
            <div
              v-if="article.tags && article.tags.length > 0"
              class="mt-10 flex flex-wrap items-center gap-2 pt-6 border-t border-[var(--border)]"
            >
              <Hash class="size-4 text-[var(--text-muted)]" />
              <router-link
                v-for="tag in article.tags"
                :key="tag.id"
                :to="`/tag/${tag.id}`"
                class="inline-flex items-center px-2.5 py-1 text-xs rounded-md border border-[var(--border)] text-[var(--text-soft)] hover:border-[var(--brand)] hover:text-[var(--brand)] hover:bg-[var(--brand-soft)] transition-colors"
              >
                #{{ tag.name }}
              </router-link>
            </div>

            <!-- 作者卡片 -->
            <div class="mt-12 relative overflow-hidden rounded-2xl border border-[var(--border)] bg-gradient-to-br from-[var(--brand-soft)]/60 via-[var(--surface)] to-[var(--surface)] p-6 sm:p-8">
              <div aria-hidden="true" class="absolute -top-12 -right-12 size-40 bg-[var(--brand)]/15 rounded-full blur-3xl"></div>
              <div class="relative flex flex-col sm:flex-row sm:items-center gap-5">
                <div class="grid place-items-center size-16 shrink-0 rounded-2xl bg-gradient-to-br from-[var(--brand)] via-[#9333ea] to-[var(--accent)] text-white text-xl font-bold shadow-[var(--shadow-md)]">
                  {{ authorInitial }}
                </div>
                <div class="flex-1 min-w-0">
                  <p class="eyebrow">Author</p>
                  <h3 class="mt-1 font-display text-xl font-semibold text-[var(--text)]">
                    {{ siteStore.config.site_author || siteStore.config.site_name }}
                  </h3>
                  <p class="mt-1 text-sm leading-relaxed text-[var(--text-soft)]">
                    {{ siteStore.config.site_description || '感谢阅读，欢迎交流！' }}
                  </p>
                </div>
                <router-link
                  to="/"
                  class="inline-flex items-center gap-1 self-start sm:self-center px-4 py-2 rounded-full text-sm font-medium text-[var(--brand)] hover:bg-[var(--brand-soft)] transition-colors"
                >
                  更多文章 <ArrowRight class="size-3.5" />
                </router-link>
              </div>
            </div>

            <!-- 评论 -->
            <div class="mt-12">
              <CommentSection v-if="canComment" :article-id="article.id" />
              <div
                v-else
                class="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 text-center text-sm text-[var(--text-soft)]"
              >
                评论功能已关闭
              </div>
            </div>
          </div>

          <!-- 侧栏（TOC + 信息） -->
          <aside class="hidden xl:block">
            <div class="sticky top-24 space-y-6">
              <!-- 目录 -->
              <div v-if="toc.length > 0" class="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-sm)]">
                <p class="eyebrow mb-3">Contents</p>
                <ul class="space-y-1.5 text-sm">
                  <li v-for="item in toc" :key="item.id">
                    <a
                      :href="`#${item.id}`"
                      :class="[
                        'block leading-snug transition-colors py-1 border-l-2 pl-3',
                        activeHeading === item.id
                          ? 'border-[var(--brand)] text-[var(--brand)] font-medium'
                          : 'border-transparent text-[var(--text-soft)] hover:text-[var(--text)] hover:border-[var(--border-strong)]',
                      ]"
                      :style="{ marginLeft: `${(item.level - 1) * 8}px` }"
                      @click="onTocClick($event, item.id)"
                    >
                      {{ item.text }}
                    </a>
                  </li>
                </ul>
              </div>

              <!-- 文章信息 -->
              <div class="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-sm)]">
                <p class="eyebrow mb-3">Info</p>
                <div class="space-y-3 text-sm">
                  <div class="flex items-center justify-between gap-4">
                    <span class="text-[var(--text-muted)]">发布</span>
                    <span class="text-[var(--text)] tabular-nums">{{ formatFriendlyTime(article.created_at) }}</span>
                  </div>
                  <div class="flex items-center justify-between gap-4">
                    <span class="text-[var(--text-muted)]">阅读量</span>
                    <span class="text-[var(--text)] tabular-nums">{{ article.view_count }}</span>
                  </div>
                  <div class="flex items-center justify-between gap-4">
                    <span class="text-[var(--text-muted)]">字数</span>
                    <span class="text-[var(--text)] tabular-nums">{{ wordCount }}</span>
                  </div>
                  <div class="flex items-center justify-between gap-4">
                    <span class="text-[var(--text-muted)]">阅读时长</span>
                    <span class="text-[var(--text)] tabular-nums">{{ readingTime }} 分钟</span>
                  </div>
                </div>
              </div>

              <!-- 回到顶部 -->
              <button
                class="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-full border border-[var(--border)] bg-[var(--surface)] text-sm font-medium text-[var(--text-soft)] hover:text-[var(--brand)] hover:border-[var(--brand)] transition-colors"
                @click="scrollTop"
              >
                <ArrowUp class="size-4" /> 回到顶部
              </button>
            </div>
          </aside>
        </div>
      </div>
    </article>

    <!-- 不存在 -->
    <div v-else class="container-page py-20">
      <UEmpty description="文章不存在或已被删除" />
    </div>

    <SiteFooter />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed, watch, nextTick, useTemplateRef } from 'vue'
import { useRoute } from 'vue-router'
import { getArticle, type Article } from '@/api/articles'
import { useMarkdown } from '@/composables/useMarkdown'
import { useSiteStore } from '@/stores/site'
import { formatFriendlyTime } from '@/utils/time'
import { ArrowUp, ArrowRight, Calendar, Eye, Folder, Hash, Clock } from 'lucide-vue-next'
import { UEmpty, USkeleton, toast } from '@/ui'
import CommentSection from '../components/CommentSection.vue'
import SiteNavbar from '../components/SiteNavbar.vue'
import SiteFooter from '../components/SiteFooter.vue'

const route = useRoute()
const { render } = useMarkdown()
const siteStore = useSiteStore()

const article = ref<Article | null>(null)
const loading = ref(false)
const articleBody = useTemplateRef<HTMLElement>('articleBody')

interface TocItem {
  id: string
  text: string
  level: number
}
const toc = ref<TocItem[]>([])
const activeHeading = ref('')
const progressPercent = ref(0)

const renderedContent = computed(() => {
  if (!article.value) return ''
  if (article.value.rendered_content) return article.value.rendered_content
  return render(article.value.content || '')
})

const canComment = computed(() => {
  if (!siteStore.config.comment_enabled) return false
  if (!article.value) return false
  return article.value.allow_comment !== false
})

const wordCount = computed(() => {
  if (!article.value) return 0
  const txt = (article.value.content || '').replace(/<[^>]+>/g, '')
  return txt.replace(/\s+/g, '').length
})

const readingTime = computed(() => Math.max(1, Math.round(wordCount.value / 350)))

const authorInitial = computed(() => {
  const name = siteStore.config.site_author || siteStore.config.site_name || 'A'
  return Array.from(name)[0]?.toUpperCase() ?? 'A'
})

const fetchArticle = async () => {
  try {
    loading.value = true
    const slug = route.params.slug as string
    const res = await getArticle(slug)
    article.value = res.data?.data ?? null
    if (article.value) {
      document.title = `${article.value.title} - ${article.value.category?.name ?? '博客'}`
      await nextTick()
      buildToc()
    }
  } catch (e) {
    console.error(e)
    toast.error('获取文章详情失败')
  } finally {
    loading.value = false
  }
}

const buildToc = () => {
  if (!articleBody.value) {
    toc.value = []
    return
  }
  const headings = articleBody.value.querySelectorAll('h2, h3, h4')
  const items: TocItem[] = []
  headings.forEach((h, i) => {
    const el = h as HTMLElement
    if (!el.id) el.id = `heading-${i}`
    const level = Number(el.tagName.replace('H', '')) - 1
    items.push({
      id: el.id,
      text: el.innerText || el.textContent || '',
      level,
    })
  })
  toc.value = items
}

const onTocClick = (e: MouseEvent, id: string) => {
  e.preventDefault()
  const el = document.getElementById(id)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    activeHeading.value = id
  }
}

const updateScrollState = () => {
  const scrollTop = window.scrollY
  const docHeight = document.documentElement.scrollHeight - window.innerHeight
  progressPercent.value = docHeight > 0 ? Math.min(100, (scrollTop / docHeight) * 100) : 0

  // 找到当前激活的 heading
  if (toc.value.length === 0) return
  const offset = 120
  let current = toc.value[0]?.id || ''
  for (const item of toc.value) {
    const el = document.getElementById(item.id)
    if (el && el.getBoundingClientRect().top - offset <= 0) {
      current = item.id
    }
  }
  activeHeading.value = current
}

const scrollTop = () => {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

watch(
  () => route.params.slug,
  (newSlug) => {
    if (newSlug) fetchArticle()
  }
)

onMounted(() => {
  fetchArticle()
  window.addEventListener('scroll', updateScrollState, { passive: true })
  updateScrollState()
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', updateScrollState)
})
</script>
