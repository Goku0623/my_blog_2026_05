<template>
  <div class="min-h-screen flex flex-col bg-[var(--bg)]">
    <SiteNavbar />

    <!-- ============================================================
         Hero — 杂志大字头部
         ============================================================ -->
    <section class="relative overflow-hidden">
      <div aria-hidden="true" class="hero-orb size-[420px] -top-32 -left-24 bg-[var(--brand)]/30"></div>
      <div aria-hidden="true" class="hero-orb size-[360px] top-10 right-[-120px] bg-[var(--accent)]/20"></div>

      <div class="container-page relative pt-14 sm:pt-20 lg:pt-28 pb-12 sm:pb-16">
        <div class="grid lg:grid-cols-[minmax(0,1fr)_auto] gap-12 lg:gap-16 items-end">
          <div class="max-w-3xl animate-fade-in-up">
            <div class="eyebrow mb-5">
              <span>{{ today }}</span>
              <span class="opacity-60">·</span>
              <span>Personal Journal</span>
            </div>

            <h1 class="hero-headline text-[clamp(2.5rem,7vw,5.5rem)] text-[var(--text)]">
              <span class="block">书写代码，</span>
              <span class="block text-gradient-brand">记录想法。</span>
            </h1>

            <p class="mt-6 max-w-xl text-base sm:text-lg leading-relaxed text-[var(--text-soft)]">
              {{ siteStore.config.site_description || '记录技术、生活与思考，专注 Web 开发、AI 应用与开源探索。' }}
            </p>

            <div class="mt-8 flex flex-wrap items-center gap-3">
              <button
                class="inline-flex items-center gap-2 h-11 px-5 rounded-full bg-[var(--text)] text-[var(--bg)] text-sm font-medium hover:opacity-90 active:scale-[0.98] transition-all shadow-[var(--shadow-md)]"
                @click="scrollToArticles"
              >
                <BookOpen class="size-4" />
                浏览文章
                <ArrowRight class="size-4" />
              </button>
              <router-link
                to="/search"
                class="inline-flex items-center gap-2 h-11 px-5 rounded-full border border-[var(--border-strong)] bg-[var(--surface)]/60 backdrop-blur text-sm font-medium text-[var(--text-soft)] hover:text-[var(--text)] hover:border-[var(--brand)] transition-colors"
              >
                <Search class="size-4" />
                搜索
              </router-link>
            </div>
          </div>

          <!-- 右侧：浮动卡片预览 -->
          <div class="relative hidden lg:block w-[340px] xl:w-[380px]">
            <div class="absolute -inset-6 bg-gradient-to-br from-[var(--brand)]/20 to-[var(--accent)]/20 blur-2xl rounded-full"></div>
            <div class="relative grid gap-4 animate-float">
              <div class="relative rounded-2xl border border-[var(--border)] bg-[var(--surface)]/90 backdrop-blur-md p-5 shadow-[var(--shadow-lg)] -rotate-2">
                <div class="flex items-center gap-2 text-[11px] text-[var(--text-muted)] mb-2">
                  <span class="inline-flex items-center gap-1">
                    <Sparkles class="size-3 text-[var(--brand)]" /> Latest
                  </span>
                  <span>·</span>
                  <span>{{ stats.total }} articles</span>
                </div>
                <p class="text-[15px] font-semibold leading-snug text-[var(--text)] line-clamp-2">
                  {{ latestArticles[0]?.title || '欢迎来到我的博客' }}
                </p>
                <p class="mt-1.5 text-xs text-[var(--text-muted)] line-clamp-2">
                  {{ latestArticles[0]?.summary || '在这里我会分享技术、生活与一些不太成熟的想法。' }}
                </p>
              </div>

              <div class="relative rounded-2xl border border-[var(--border)] bg-[var(--surface)]/90 backdrop-blur-md p-5 shadow-[var(--shadow-lg)] rotate-2 ml-8">
                <div class="flex items-center gap-2 text-[11px] text-[var(--text-muted)] mb-2">
                  <Hash class="size-3 text-[var(--accent)]" /> Topics
                </div>
                <div class="flex flex-wrap gap-1.5">
                  <span
                    v-for="tag in tags.slice(0, 6)"
                    :key="tag.id"
                    class="text-[11px] px-2 py-0.5 rounded-md bg-[var(--bg-muted)] text-[var(--text-soft)]"
                  >
                    #{{ tag.name }}
                  </span>
                  <span v-if="!tags.length" class="text-[11px] text-[var(--text-muted)]">暂无标签</span>
                </div>
              </div>

              <div class="relative rounded-2xl border border-[var(--border)] bg-gradient-to-br from-[var(--brand)] to-[var(--accent)] p-5 text-white shadow-[var(--shadow-lg)] -rotate-1 mr-4">
                <div class="flex items-center gap-2 text-[11px] opacity-90 mb-2">
                  <CloudSun class="size-3" /> Now in {{ weather.city || '深圳' }}
                </div>
                <div v-if="weatherLoading" class="space-y-2">
                  <div class="h-5 w-24 rounded bg-white/30 animate-pulse-soft"></div>
                  <div class="h-3 w-32 rounded bg-white/20 animate-pulse-soft"></div>
                </div>
                <template v-else>
                  <p class="text-2xl font-bold leading-tight">{{ weather.temperatureText }}</p>
                  <p class="text-[12px] opacity-90 mt-1">
                    {{ weather.description }} · 体感 {{ weather.feelsLikeText }}
                  </p>
                </template>
              </div>
            </div>
          </div>
        </div>

        <!-- 数据条（极简） -->
        <div class="mt-14 sm:mt-20 grid grid-cols-2 sm:grid-cols-4 gap-px overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--border)]">
          <div class="bg-[var(--surface)]/80 backdrop-blur p-5 sm:p-6">
            <p class="text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">文章</p>
            <p class="mt-2 font-display text-3xl font-bold text-[var(--text)] tabular-nums">{{ stats.total }}</p>
          </div>
          <div class="bg-[var(--surface)]/80 backdrop-blur p-5 sm:p-6">
            <p class="text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">分类</p>
            <p class="mt-2 font-display text-3xl font-bold text-[var(--text)] tabular-nums">{{ categories.length }}</p>
          </div>
          <div class="bg-[var(--surface)]/80 backdrop-blur p-5 sm:p-6">
            <p class="text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">标签</p>
            <p class="mt-2 font-display text-3xl font-bold text-[var(--text)] tabular-nums">{{ tags.length }}</p>
          </div>
          <div class="bg-[var(--surface)]/80 backdrop-blur p-5 sm:p-6">
            <p class="text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">阅读量</p>
            <p class="mt-2 font-display text-3xl font-bold text-[var(--text)] tabular-nums">{{ formatNumber(totalViews) }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ============================================================
         Featured：精选文章
         ============================================================ -->
    <section v-if="featuredArticle" class="container-page py-10 sm:py-14">
      <div class="mb-6 flex items-end justify-between">
        <div>
          <p class="eyebrow">Editor's Pick</p>
          <h2 class="mt-2 font-display text-2xl sm:text-3xl font-bold tracking-tight text-[var(--text)]">
            精选阅读
          </h2>
        </div>
      </div>
      <ArticleCard :article="featuredArticle" variant="featured" />
    </section>

    <!-- ============================================================
         主体：文章列表 + 侧栏
         ============================================================ -->
    <main ref="articlesAnchor" class="container-page flex-1 pb-20">
      <div class="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_320px] gap-10 lg:gap-14">
        <!-- 文章列表 -->
        <section>
          <header class="mb-7 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between border-b border-[var(--border)] pb-5">
            <div>
              <p class="eyebrow">Latest</p>
              <h2 class="mt-2 font-display text-2xl sm:text-3xl font-bold tracking-tight text-[var(--text)]">
                最新文章
              </h2>
              <p class="mt-1 text-sm text-[var(--text-muted)] tabular-nums">
                共 {{ total }} 篇 · 第 {{ currentPage }} / {{ Math.max(1, Math.ceil(total / pageSize)) }} 页
              </p>
            </div>
            <div class="w-full sm:w-72">
              <UInput
                v-model="searchKeyword"
                placeholder="按 Enter 在站内搜索…"
                size="md"
                :prefix-icon="Search"
                @keyup.enter="handleSearch"
              />
            </div>
          </header>

          <div v-if="loading" class="grid gap-6 sm:grid-cols-2">
            <USkeleton v-for="i in 4" :key="i" class="h-72 rounded-2xl" />
          </div>

          <div v-else-if="articles.length > 0" class="grid gap-6 sm:grid-cols-2">
            <ArticleCard
              v-for="article in articles"
              :key="article.id"
              :article="article"
            />
          </div>

          <UEmpty v-else description="暂无文章">
            <p class="text-xs text-[var(--text-muted)]">先在管理后台创建一篇文章吧</p>
          </UEmpty>

          <div v-if="!loading && articles.length > 0 && total > pageSize" class="mt-10 flex justify-center">
            <UPagination
              v-model:current="currentPage"
              :page-size="pageSize"
              :total="total"
              @change="handlePageChange"
            />
          </div>
        </section>

        <!-- 侧栏 -->
        <aside class="space-y-7 lg:sticky lg:top-24 self-start">
          <!-- 关于卡 -->
          <div class="relative overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-[var(--shadow-sm)]">
            <div aria-hidden="true" class="absolute -top-12 -right-12 size-32 bg-[var(--brand)]/15 rounded-full blur-2xl"></div>
            <p class="eyebrow">About</p>
            <h3 class="mt-2 font-display text-lg font-semibold text-[var(--text)]">
              你好 👋
            </h3>
            <p class="mt-2 text-sm leading-relaxed text-[var(--text-soft)]">
              欢迎来到 <span class="font-medium text-[var(--text)]">{{ siteStore.config.site_name }}</span>，这里记录我学习与思考的一切。
            </p>
            <router-link
              to="/search"
              class="mt-4 inline-flex items-center gap-1 text-sm font-medium text-[var(--brand)] hover:gap-2 transition-all"
            >
              开始探索 <ArrowRight class="size-3.5" />
            </router-link>
          </div>

          <!-- 分类 -->
          <div class="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-sm)]">
            <div class="flex items-center justify-between mb-3">
              <p class="eyebrow">Categories</p>
              <Folder class="size-3.5 text-[var(--text-muted)]" />
            </div>
            <div class="space-y-1">
              <router-link
                v-for="cat in categories"
                :key="cat.id"
                :to="`/category/${cat.id}`"
                class="group flex items-center justify-between rounded-lg px-3 py-2 text-sm text-[var(--text-soft)] hover:bg-[var(--bg-muted)] hover:text-[var(--text)] transition-colors"
              >
                <span class="truncate flex items-center gap-2">
                  <span class="inline-block size-1.5 rounded-full bg-[var(--brand)]/50 group-hover:bg-[var(--brand)] transition-colors"></span>
                  {{ cat.name }}
                </span>
                <span class="text-xs text-[var(--text-muted)] tabular-nums">{{ cat.article_count }}</span>
              </router-link>
              <p v-if="categories.length === 0" class="px-3 py-2 text-xs text-[var(--text-muted)]">暂无分类</p>
            </div>
          </div>

          <!-- 标签云 -->
          <div class="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-sm)]">
            <div class="flex items-center justify-between mb-3">
              <p class="eyebrow">Tags</p>
              <Hash class="size-3.5 text-[var(--text-muted)]" />
            </div>
            <div class="flex flex-wrap gap-1.5">
              <router-link
                v-for="tag in tags"
                :key="tag.id"
                :to="`/tag/${tag.id}`"
                class="inline-flex items-center px-2.5 py-1 text-xs rounded-md border border-[var(--border)] text-[var(--text-soft)] hover:border-[var(--brand)] hover:text-[var(--brand)] hover:bg-[var(--brand-soft)] transition-colors"
              >
                #{{ tag.name }}
              </router-link>
              <p v-if="tags.length === 0" class="text-xs text-[var(--text-muted)]">暂无标签</p>
            </div>
          </div>

          <!-- 最新文章 compact -->
          <div class="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-sm)]">
            <div class="flex items-center justify-between mb-2">
              <p class="eyebrow">Recent</p>
              <BookOpen class="size-3.5 text-[var(--text-muted)]" />
            </div>
            <div class="divide-y divide-[var(--border)]">
              <ArticleCard
                v-for="art in latestArticles"
                :key="art.id"
                :article="art"
                variant="compact"
              />
              <p v-if="latestArticles.length === 0" class="py-3 text-xs text-[var(--text-muted)]">暂无文章</p>
            </div>
          </div>
        </aside>
      </div>
    </main>

    <SiteFooter />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, useTemplateRef } from 'vue'
import { useRouter } from 'vue-router'
import { getArticles, getCategories, getTags, type Article, type Category, type Tag } from '@/api/articles'
import { getWeather } from '@/api/ai'
import { useSiteStore } from '@/stores/site'
import {
  Sparkles, Search, Folder, Hash, BookOpen, CloudSun, ArrowRight,
} from 'lucide-vue-next'
import { UInput, UEmpty, USkeleton, UPagination, toast } from '@/ui'
import ArticleCard from '../components/ArticleCard.vue'
import SiteNavbar from '../components/SiteNavbar.vue'
import SiteFooter from '../components/SiteFooter.vue'

const router = useRouter()
const siteStore = useSiteStore()

const articlesAnchor = useTemplateRef<HTMLElement>('articlesAnchor')

const searchKeyword = ref('')
const articles = ref<Article[]>([])
const latestArticles = ref<Article[]>([])
const featuredArticle = ref<Article | null>(null)
const categories = ref<Category[]>([])
const tags = ref<Tag[]>([])

const currentPage = ref(1)
const pageSize = ref(8)
const total = ref(0)
const loading = ref(false)
const weatherLoading = ref(false)
const weather = ref({
  city: '深圳市',
  description: '获取天气中',
  temperatureText: '--',
  feelsLikeText: '--',
  humidityText: '--',
})

const stats = computed(() => ({ total: total.value }))
const totalViews = computed(() =>
  articles.value.reduce((acc, a) => acc + (a.view_count ?? 0), 0)
    + latestArticles.value.reduce((acc, a) => acc + (a.view_count ?? 0), 0)
)

const today = computed(() =>
  new Date().toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
)

const formatNumber = (n: number) => {
  if (n >= 10000) return `${(n / 10000).toFixed(1)}w`
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`
  return String(n)
}

const fetchArticles = async () => {
  try {
    loading.value = true
    const res = await getArticles({
      page: currentPage.value,
      page_size: pageSize.value,
      is_published: true,
    })
    const data = res.data?.data ?? { items: [], total: 0 }
    articles.value = data.items ?? []
    total.value = data.total ?? 0
  } catch (e) {
    console.error(e)
    toast.error('获取文章列表失败')
  } finally {
    loading.value = false
  }
}

const fetchLatestArticles = async () => {
  try {
    const res = await getArticles({ page: 1, page_size: 5, is_published: true })
    const items = res.data?.data?.items ?? []
    latestArticles.value = items
    const featured = items.find((a) => a.is_featured)
    featuredArticle.value = featured || items[0] || null
  } catch (e) {
    console.warn('获取最新文章失败', e)
  }
}

const fetchCategoriesAndTags = async () => {
  try {
    const [catRes, tagRes] = await Promise.all([getCategories(), getTags()])
    categories.value = catRes.data?.data ?? []
    tags.value = tagRes.data?.data ?? []
  } catch (e) {
    console.warn('获取分类/标签失败', e)
  }
}

const handleSearch = () => {
  if (searchKeyword.value.trim()) {
    router.push({ path: '/search', query: { q: searchKeyword.value.trim() } })
  }
}

const handlePageChange = () => {
  scrollToArticles()
  fetchArticles()
}

const scrollToArticles = () => {
  articlesAnchor.value?.scrollIntoView({ behavior: 'smooth' })
}

const fetchWeather = async () => {
  try {
    weatherLoading.value = true
    const res = await getWeather({ city: '440300' })
    const data = res.data?.data
    weather.value = {
      city: data?.city || '未知城市',
      description: data?.description || '未知天气',
      temperatureText: typeof data?.temperature === 'number' ? `${Math.round(data.temperature)}°C` : '--',
      feelsLikeText: typeof data?.feels_like === 'number' ? `${Math.round(data.feels_like)}°C` : '--',
      humidityText: typeof data?.humidity === 'number' ? `${data.humidity}%` : '--',
    }
  } catch (e) {
    console.warn('获取天气失败', e)
  } finally {
    weatherLoading.value = false
  }
}

onMounted(() => {
  fetchArticles()
  fetchLatestArticles()
  fetchCategoriesAndTags()
  fetchWeather()
})
</script>
