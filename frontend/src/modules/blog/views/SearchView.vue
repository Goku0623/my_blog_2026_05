<template>
  <div class="min-h-screen flex flex-col bg-[var(--bg)]">
    <SiteNavbar />

    <!-- Hero / 搜索表单 -->
    <section class="relative overflow-hidden">
      <div aria-hidden="true" class="hero-orb size-[420px] -top-32 left-1/2 -translate-x-1/2 bg-[var(--brand)]/15"></div>

      <div class="container-page relative pt-12 sm:pt-16 pb-10">
        <div class="text-center max-w-3xl mx-auto">
          <span class="eyebrow"><SearchIcon class="size-3" /> 探索</span>
          <h1 class="mt-3 hero-headline text-[clamp(2rem,5vw,3.75rem)] text-[var(--text)] leading-[1.1]">
            搜索<span class="text-gradient-brand">想要的内容</span>
          </h1>
          <p class="mt-4 text-base text-[var(--text-soft)]">
            输入关键词，从所有文章中找到你感兴趣的内容
          </p>
        </div>

        <form class="mx-auto mt-10 max-w-2xl" @submit.prevent="onSearch">
          <div class="flex items-center gap-2 rounded-2xl border border-[var(--border)] bg-[var(--surface)]/80 backdrop-blur p-2 shadow-[var(--shadow-md)] focus-within:ring-2 focus-within:ring-[var(--brand)]/30 focus-within:border-[var(--brand)]/40 transition-all">
            <div class="grid place-items-center size-10 shrink-0 text-[var(--text-muted)]">
              <SearchIcon class="size-5" />
            </div>
            <input
              v-model="input"
              type="text"
              placeholder="输入关键词，比如「Vue」「FastAPI」「AI」…"
              class="flex-1 bg-transparent outline-none text-base text-[var(--text)] placeholder:text-[var(--text-muted)] py-2"
            />
            <button
              type="submit"
              class="inline-flex items-center gap-1.5 h-10 px-5 rounded-xl bg-gradient-to-br from-[var(--brand)] to-[var(--accent)] text-white text-sm font-medium shadow-[var(--shadow-md)] hover:opacity-95 active:scale-[0.98] transition-all"
            >
              搜索
              <ArrowRight class="size-4" />
            </button>
          </div>

          <div class="mt-4 flex flex-wrap items-center justify-center gap-3 text-xs text-[var(--text-muted)]">
            <div class="flex flex-wrap items-center gap-1.5">
              <span>范围:</span>
              <button
                v-for="opt in searchInOptions"
                :key="opt.value"
                type="button"
                :class="[
                  'px-2.5 py-1 rounded-full border transition-colors',
                  searchIn === opt.value
                    ? 'border-[var(--brand)] text-[var(--brand)] bg-[var(--brand-soft)]'
                    : 'border-[var(--border)] hover:border-[var(--border-strong)]',
                ]"
                @click="searchIn = opt.value"
              >{{ opt.label }}</button>
            </div>

            <div class="flex flex-wrap items-center gap-1.5">
              <span>时间:</span>
              <button
                v-for="opt in timeFilterOptions"
                :key="opt.value"
                type="button"
                :class="[
                  'px-2.5 py-1 rounded-full border transition-colors',
                  timeFilter === opt.value
                    ? 'border-[var(--brand)] text-[var(--brand)] bg-[var(--brand-soft)]'
                    : 'border-[var(--border)] hover:border-[var(--border-strong)]',
                ]"
                @click="timeFilter = opt.value"
              >{{ opt.label }}</button>
            </div>
          </div>
        </form>

        <div v-if="keyword" class="mt-10 text-center text-sm text-[var(--text-muted)]">
          关键词
          <span class="px-2 py-0.5 rounded-md bg-[var(--brand-soft)] text-[var(--brand)] font-medium mx-1">{{ keyword }}</span>
          共匹配
          <span class="font-semibold text-[var(--brand)] tabular-nums mx-1">{{ total }}</span>
          篇文章
        </div>
      </div>
    </section>

    <main class="flex-1 container-page pb-20">
      <div v-if="loading" class="grid gap-6 sm:grid-cols-2">
        <USkeleton v-for="i in 4" :key="i" class="h-72 rounded-2xl" />
      </div>
      <UEmpty
        v-else-if="!articles.length && keyword"
        title="没有找到匹配的文章"
        description="换个关键词试试吧"
        class="py-20"
      />
      <div v-else-if="!keyword" class="text-center py-20 text-sm text-[var(--text-muted)]">
        <SearchIcon class="size-8 mx-auto mb-3 opacity-50" />
        请输入关键词开始搜索
      </div>
      <div v-else class="grid gap-6 sm:grid-cols-2">
        <ArticleCard v-for="a in articles" :key="a.id" :article="a" />
      </div>

      <div v-if="total > pageSize" class="mt-10 flex justify-center">
        <UPagination :current="page" :total="total" :page-size="pageSize" @update:current="page = $event; fetchData()" />
      </div>
    </main>

    <SiteFooter />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search as SearchIcon, ArrowRight } from 'lucide-vue-next'
import { searchArticles, type Article } from '@/api/articles'
import SiteNavbar from '../components/SiteNavbar.vue'
import SiteFooter from '../components/SiteFooter.vue'
import ArticleCard from '../components/ArticleCard.vue'
import { UEmpty, USkeleton, UPagination, toast } from '@/ui'

const route = useRoute()
const router = useRouter()

const resolveKeyword = () => {
  const q = String(route.query.q || '').trim()
  const legacyKeyword = String(route.query.keyword || '').trim()
  const tagKeyword = String(route.query.tag || '').trim()
  return q || legacyKeyword || tagKeyword
}

const keyword = ref<string>(resolveKeyword())
const input = ref<string>(keyword.value)
const searchIn = ref<'title' | 'summary' | 'title_summary'>('title_summary')
const timeFilter = ref<'all' | '7d' | '30d' | '90d' | '365d'>('all')
const articles = ref<Article[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)

const searchInOptions: { label: string; value: 'title' | 'summary' | 'title_summary' }[] = [
  { label: '标题 + 摘要', value: 'title_summary' },
  { label: '仅标题', value: 'title' },
  { label: '仅摘要', value: 'summary' },
]

const timeFilterOptions: { label: string; value: 'all' | '7d' | '30d' | '90d' | '365d' }[] = [
  { label: '全部', value: 'all' },
  { label: '7 天', value: '7d' },
  { label: '30 天', value: '30d' },
  { label: '90 天', value: '90d' },
  { label: '1 年', value: '365d' },
]

const resolveSearchIn = () => {
  const raw = String(route.query.search_in || '').trim()
  if (raw === 'title' || raw === 'summary' || raw === 'title_summary') return raw
  return 'title_summary'
}

const resolveTimeFilter = () => {
  const raw = String(route.query.time_filter || '').trim()
  if (raw === '7d' || raw === '30d' || raw === '90d' || raw === '365d' || raw === 'all') return raw
  return 'all'
}

const fetchData = async () => {
  if (!keyword.value.trim()) {
    articles.value = []
    total.value = 0
    return
  }
  loading.value = true
  try {
    const res = await searchArticles({
      keyword: keyword.value.trim(),
      page: page.value,
      page_size: pageSize.value,
      search_in: searchIn.value,
      time_filter: timeFilter.value,
    })
    const data = res.data?.data ?? { items: [], total: 0 }
    articles.value = data.items || []
    total.value = data.total || 0
  } catch {
    toast.error('搜索失败，请稍后再试')
  } finally {
    loading.value = false
  }
}

const onSearch = () => {
  if (!input.value.trim()) return
  router.push({
    path: '/search',
    query: {
      q: input.value.trim(),
      search_in: searchIn.value,
      time_filter: timeFilter.value,
    },
  })
}

watch(
  () => [route.query.q, route.query.keyword, route.query.tag, route.query.search_in, route.query.time_filter],
  () => {
    keyword.value = resolveKeyword()
    searchIn.value = resolveSearchIn()
    timeFilter.value = resolveTimeFilter()
    input.value = keyword.value
    page.value = 1
    fetchData()
  }
)

onMounted(() => {
  searchIn.value = resolveSearchIn()
  timeFilter.value = resolveTimeFilter()
  fetchData()
})
</script>
