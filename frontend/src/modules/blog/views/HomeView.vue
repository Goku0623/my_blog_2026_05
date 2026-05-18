<template>
  <div class="min-h-screen flex flex-col bg-[var(--bg)]">
    <SiteNavbar />

    <!-- ============================================================
         Hero
         ============================================================ -->
    <section class="relative overflow-hidden">
      <div aria-hidden="true" class="hero-orb size-[420px] -top-32 -left-24 bg-[var(--brand)]/30"></div>
      <div aria-hidden="true" class="hero-orb size-[360px] top-10 right-[-120px] bg-[var(--accent)]/20"></div>

      <div class="container-page relative pt-14 sm:pt-20 lg:pt-28 pb-12 sm:pb-16">
        <div class="grid lg:grid-cols-[minmax(0,1fr)_auto] gap-12 lg:gap-16 items-end">
          <div class="max-w-3xl animate-fade-in-up">
            <div class="eyebrow mb-5">
              <span>{{ today }}</span>
              <span class="opacity-60">&middot;</span>
              <span>Personal Journal</span>
            </div>

            <h1 class="hero-headline text-[clamp(2.5rem,7vw,5.5rem)] text-[var(--text)]">
              <span class="block">{{ '\u4e66\u5199\u4ee3\u7801\uff0c' }}</span>
              <span class="block text-gradient-brand">{{ '\u8bb0\u5f55\u60f3\u6cd5\u3002' }}</span>
            </h1>

            <p class="mt-6 max-w-xl text-base sm:text-lg leading-relaxed text-[var(--text-soft)]">
              {{ siteStore.config.site_description || '\u8bb0\u5f55\u6280\u672f\u3001\u751f\u6d3b\u4e0e\u601d\u8003\uff0c\u4e13\u6ce8 Web \u5f00\u53d1\u3001AI \u5e94\u7528\u4e0e\u5f00\u6e90\u63a2\u7d22\u3002' }}
            </p>

            <div class="mt-8 flex flex-wrap items-center gap-3">
              <button
                class="inline-flex items-center gap-2 h-11 px-5 rounded-full bg-[var(--text)] text-[var(--bg)] text-sm font-medium hover:opacity-90 active:scale-[0.98] transition-all shadow-[var(--shadow-md)]"
                @click="scrollToArticles"
              >
                <BookOpen class="size-4" />
                {{ '\u6d4f\u89c8\u6587\u7ae0' }}
                <ArrowRight class="size-4" />
              </button>
            </div>
          </div>

          <!-- Preview Cards -->
          <div class="relative hidden lg:block w-[340px] xl:w-[380px]">
            <div class="absolute -inset-6 bg-gradient-to-br from-[var(--brand)]/20 to-[var(--accent)]/20 blur-2xl rounded-full"></div>
            <div class="relative grid gap-4 animate-float">
              <div class="relative rounded-2xl border border-[var(--border)] bg-[var(--surface)]/90 backdrop-blur-md p-5 shadow-[var(--shadow-lg)] -rotate-2">
                <div class="flex items-center gap-2 text-[11px] text-[var(--text-muted)] mb-2">
                  <span class="inline-flex items-center gap-1">
                    <Sparkles class="size-3 text-[var(--brand)]" /> Latest
                  </span>
                  <span>&middot;</span>
                  <span>{{ stats.total }} articles</span>
                </div>
                <p class="text-[15px] font-semibold leading-snug text-[var(--text)] line-clamp-2">
                  {{ latestArticles[0]?.title || '\u6b22\u8fce\u6765\u5230\u6211\u7684\u535a\u5ba2' }}
                </p>
                <p class="mt-1.5 text-xs text-[var(--text-muted)] line-clamp-2">
                  {{ latestArticles[0]?.summary || '\u5728\u8fd9\u91cc\u6211\u4f1a\u5206\u4eab\u6280\u672f\u3001\u751f\u6d3b\u4e0e\u4e00\u4e9b\u4e0d\u592a\u6210\u719f\u7684\u60f3\u6cd5\u3002' }}
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
                  <span v-if="!tags.length" class="text-[11px] text-[var(--text-muted)]">{{ '\u6682\u65e0\u6807\u7b7e' }}</span>
                </div>
              </div>

              <div class="relative rounded-2xl border border-[var(--border)] bg-gradient-to-br from-[var(--brand)] to-[var(--accent)] p-5 text-white shadow-[var(--shadow-lg)] -rotate-1 mr-4">
                <div class="flex items-center gap-2 text-[11px] opacity-90 mb-2">
                  <CloudSun class="size-3" /> Now in {{ weather.city || weatherDisplayName }}
                </div>
                <div v-if="weatherLoading" class="space-y-2">
                  <div class="h-5 w-24 rounded bg-white/30 animate-pulse-soft"></div>
                  <div class="h-3 w-32 rounded bg-white/20 animate-pulse-soft"></div>
                </div>
                <template v-else>
                  <p class="text-2xl font-bold leading-tight">{{ weather.temperatureText }}</p>
                  <p class="text-[12px] opacity-90 mt-1">
                    {{ weather.description }} &middot; {{ '\u4f53\u611f' }} {{ weather.feelsLikeText }}
                  </p>
                </template>
              </div>
            </div>
          </div>
        </div>

        <!-- Stats -->
        <div class="mt-14 sm:mt-20 grid grid-cols-2 sm:grid-cols-4 gap-px overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--border)]">
          <div class="bg-[var(--surface)]/80 backdrop-blur p-5 sm:p-6">
            <p class="text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">{{ '\u6587\u7ae0' }}</p>
            <p class="mt-2 font-display text-3xl font-bold text-[var(--text)] tabular-nums">{{ stats.total }}</p>
          </div>
          <div class="bg-[var(--surface)]/80 backdrop-blur p-5 sm:p-6">
            <p class="text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">{{ '\u5206\u7c7b' }}</p>
            <p class="mt-2 font-display text-3xl font-bold text-[var(--text)] tabular-nums">{{ categories.length }}</p>
          </div>
          <div class="bg-[var(--surface)]/80 backdrop-blur p-5 sm:p-6">
            <p class="text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">{{ '\u6807\u7b7e' }}</p>
            <p class="mt-2 font-display text-3xl font-bold text-[var(--text)] tabular-nums">{{ tags.length }}</p>
          </div>
          <div class="bg-[var(--surface)]/80 backdrop-blur p-5 sm:p-6">
            <p class="text-[11px] uppercase tracking-[0.18em] text-[var(--text-muted)]">{{ '\u9605\u8bfb\u91cf' }}</p>
            <p class="mt-2 font-display text-3xl font-bold text-[var(--text)] tabular-nums">{{ formatNumber(totalViews) }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ============================================================
         Featured
         ============================================================ -->
    <section v-if="featuredTotal > 0" class="container-page py-10 sm:py-14">
      <div class="mb-6 flex items-end justify-between">
        <div>
          <p class="eyebrow">Editor's Pick</p>
          <h2 class="mt-2 font-display text-2xl sm:text-3xl font-bold tracking-tight text-[var(--text)]">
            {{ '\u7cbe\u9009\u9605\u8bfb' }}
          </h2>
        </div>
      </div>
      <ArticleCard v-if="featuredArticle" :article="featuredArticle" variant="featured" />
      <div v-if="featuredTotal > featuredPageSize" class="mt-8 flex justify-center">
        <UPagination
          v-model:current="featuredCurrentPage"
          :page-size="featuredPageSize"
          :total="featuredTotal"
          @change="handleFeaturedPageChange"
        />
      </div>
    </section>

    <!-- ============================================================
         Main Content
         ============================================================ -->
    <main ref="articlesAnchor" class="container-page flex-1 pb-20">
      <div class="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_380px] gap-10 lg:gap-14">
        <!-- Articles -->
        <section>
          <header class="mb-7 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between border-b border-[var(--border)] pb-5">
            <div>
              <p class="eyebrow">Latest</p>
              <h2 class="mt-2 font-display text-2xl sm:text-3xl font-bold tracking-tight text-[var(--text)]">
                {{ '\u6700\u65b0\u6587\u7ae0' }}
              </h2>
              <p class="mt-1 text-sm text-[var(--text-muted)] tabular-nums">
                {{ '\u5171' }} {{ total }} {{ '\u7bc7' }} &middot; {{ '\u7b2c' }} {{ currentPage }} / {{ Math.max(1, Math.ceil(total / pageSize)) }} {{ '\u9875' }}
              </p>
            </div>
          </header>

          <div v-if="loading" class="article-list-grid">
            <USkeleton v-for="i in 4" :key="i" class="h-[440px] rounded-2xl" />
          </div>

          <div v-else-if="articles.length > 0" class="article-list-grid">
            <ArticleCard
              v-for="article in articles"
              :key="article.id"
              :article="article"
            />
          </div>

          <UEmpty v-else :description="'\u6682\u65e0\u6587\u7ae0'">
            <p class="text-xs text-[var(--text-muted)]">{{ '\u5148\u5728\u7ba1\u7406\u540e\u53f0\u521b\u5efa\u4e00\u7bc7\u6587\u7ae0\u5427' }}</p>
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

        <!-- Sidebar -->
        <aside class="space-y-7 lg:sticky lg:top-24 self-start">
          <!-- Categories -->
          <div class="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-[var(--shadow-sm)]">
            <div class="flex items-center justify-between mb-4">
              <p class="eyebrow text-xs">Categories</p>
              <Folder class="size-4 text-[var(--text-muted)]" />
            </div>
            <div class="space-y-2">
              <router-link
                v-for="cat in categories"
                :key="cat.id"
                :to="`/category/${cat.id}`"
                class="group flex items-center justify-between rounded-xl px-4 py-3 text-[15px] text-[var(--text-soft)] hover:bg-[var(--bg-muted)] hover:text-[var(--text)] transition-colors"
              >
                <span class="truncate flex items-center gap-2">
                  <span class="inline-block size-2 rounded-full bg-[var(--brand)]/50 group-hover:bg-[var(--brand)] transition-colors"></span>
                  {{ cat.name }}
                </span>
                <span class="text-sm text-[var(--text-muted)] tabular-nums">{{ cat.article_count }}</span>
              </router-link>
              <p v-if="categories.length === 0" class="px-4 py-3 text-sm text-[var(--text-muted)]">{{ '\u6682\u65e0\u5206\u7c7b' }}</p>
            </div>
          </div>

          <!-- Tags -->
          <div class="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 shadow-[var(--shadow-sm)]">
            <div class="flex items-center justify-between mb-4">
              <p class="eyebrow text-xs">Tags</p>
              <Hash class="size-4 text-[var(--text-muted)]" />
            </div>
            <div class="flex flex-wrap gap-2">
              <router-link
                v-for="tag in tags"
                :key="tag.id"
                :to="`/tag/${tag.id}`"
                class="inline-flex items-center px-3 py-1.5 text-sm rounded-lg border border-[var(--border)] text-[var(--text-soft)] hover:border-[var(--brand)] hover:text-[var(--brand)] hover:bg-[var(--brand-soft)] transition-colors"
              >
                #{{ tag.name }}
              </router-link>
              <p v-if="tags.length === 0" class="text-sm text-[var(--text-muted)]">{{ '\u6682\u65e0\u6807\u7b7e' }}</p>
            </div>
          </div>

        </aside>
      </div>
    </main>

    <SiteFooter />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, useTemplateRef } from 'vue'
import {
  getHomeAggregate,
  type Article,
  type Category,
  type Tag,
} from '@/api/articles'
import { getWeather } from '@/api/ai'
import { useSiteStore } from '@/stores/site'
import {
  Sparkles, Folder, Hash, CloudSun, ArrowRight, BookOpen,
} from 'lucide-vue-next'
import { UEmpty, USkeleton, UPagination, toast } from '@/ui'
import ArticleCard from '../components/ArticleCard.vue'
import SiteNavbar from '../components/SiteNavbar.vue'
import SiteFooter from '../components/SiteFooter.vue'

const siteStore = useSiteStore()

const articlesAnchor = useTemplateRef<HTMLElement>('articlesAnchor')

const articles = ref<Article[]>([])
const latestArticles = ref<Article[]>([])
const featuredArticle = ref<Article | null>(null)
const featuredCurrentPage = ref(1)
const featuredPageSize = ref(1)
const featuredTotal = ref(0)
const categories = ref<Category[]>([])
const tags = ref<Tag[]>([])

const currentPage = ref(1)
const pageSize = ref(6)
const total = ref(0)
const totalViews = ref(0)
const loading = ref(false)
const weatherLoading = ref(false)
const weather = ref({
  city: '\u6df1\u5733\u5e02',
  description: '\u83b7\u53d6\u5929\u6c14\u4e2d',
  temperatureText: '--',
  feelsLikeText: '--',
  humidityText: '--',
})
let weatherDelayTimer: number | null = null

const stats = computed(() => ({ total: total.value }))
const weatherDisplayName = computed(() => siteStore.config.weather_city_name || '\u6df1\u5733\u5e02')
const weatherCityCode = computed(() => siteStore.config.weather_city_code || '440300')

const today = computed(() =>
  new Date().toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
)

const formatNumber = (n: number) => {
  return n.toLocaleString('zh-CN')
}

const fetchHomeAggregate = async (showLoading = true) => {
  try {
    if (showLoading) loading.value = true
    const res = await getHomeAggregate({
      page: currentPage.value,
      page_size: pageSize.value,
      featured_page: featuredCurrentPage.value,
      featured_page_size: featuredPageSize.value,
    })
    const data = res.data?.data
    if (!data) return

    const articlesData = data.articles ?? { items: [], total: 0 }
    const featuredData = data.featured ?? { items: [], total: 0 }
    articles.value = articlesData.items ?? []
    total.value = articlesData.total ?? 0
    latestArticles.value = data.latest_items ?? []
    featuredArticle.value = (featuredData.items ?? [])[0] || null
    featuredTotal.value = featuredData.total ?? 0
    categories.value = data.categories ?? []
    tags.value = data.tags ?? []
    totalViews.value = data.total_views ?? totalViews.value
  } catch (e) {
    console.error(e)
    toast.error('\u83b7\u53d6\u9996\u9875\u6570\u636e\u5931\u8d25')
  } finally {
    if (showLoading) loading.value = false
  }
}

const handlePageChange = () => {
  scrollToArticles()
  void fetchHomeAggregate(true)
}

const handleFeaturedPageChange = () => {
  void fetchHomeAggregate(false)
}

const scrollToArticles = () => {
  articlesAnchor.value?.scrollIntoView({ behavior: 'smooth' })
}

const fetchWeather = async () => {
  try {
    weatherLoading.value = true
    const res = await getWeather({ city: weatherCityCode.value })
    const data = res.data?.data
    weather.value = {
      city: data?.city || weatherDisplayName.value || '\u672a\u77e5\u57ce\u5e02',
      description: data?.description || '\u672a\u77e5\u5929\u6c14',
      temperatureText: typeof data?.temperature === 'number' ? `${Math.round(data.temperature)}\u00b0C` : '--',
      feelsLikeText: typeof data?.feels_like === 'number' ? `${Math.round(data.feels_like)}\u00b0C` : '--',
      humidityText: typeof data?.humidity === 'number' ? `${data.humidity}%` : '--',
    }
  } catch (e) {
    console.warn('\u83b7\u53d6\u5929\u6c14\u5931\u8d25', e)
  } finally {
    weatherLoading.value = false
  }
}

const scheduleWeatherFetch = () => {
  if (weatherDelayTimer !== null) {
    window.clearTimeout(weatherDelayTimer)
  }
  const idleCb = (window as Window & { requestIdleCallback?: (cb: () => void, options?: { timeout: number }) => number }).requestIdleCallback
  if (typeof idleCb === 'function') {
    idleCb(() => {
      void fetchWeather()
    }, { timeout: 3000 })
    return
  }
  weatherDelayTimer = window.setTimeout(() => {
    weatherDelayTimer = null
    void fetchWeather()
  }, 2500)
}

onMounted(async () => {
  await fetchHomeAggregate(true)
  scheduleWeatherFetch()
})

onBeforeUnmount(() => {
  if (weatherDelayTimer !== null) {
    window.clearTimeout(weatherDelayTimer)
    weatherDelayTimer = null
  }
})
</script>
