<template>
  <div class="min-h-screen flex flex-col bg-[var(--bg)]">
    <SiteNavbar />

    <!-- Hero -->
    <section class="relative overflow-hidden">
      <div aria-hidden="true" class="hero-orb size-[400px] -top-32 -right-24 bg-[var(--accent)]/20"></div>
      <div aria-hidden="true" class="hero-orb size-[320px] top-0 left-[-100px] bg-[var(--brand)]/15"></div>

      <div class="container-page relative pt-12 sm:pt-16 pb-10">
        <div class="max-w-3xl">
          <div class="flex items-center gap-2 mb-4">
            <span class="eyebrow"><Folder class="size-3" /> 分类</span>
          </div>
          <h1 class="hero-headline text-[clamp(2rem,5vw,3.75rem)] text-[var(--text)] leading-[1.1]">
            <span class="text-gradient-brand">{{ category?.name || '加载中…' }}</span>
          </h1>
          <p class="mt-6 flex items-center gap-3 text-sm text-[var(--text-muted)]">
            <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-[var(--border)] bg-[var(--surface)]/60">
              <FileText class="size-3.5" />
              <span class="tabular-nums">{{ total }}</span>
              <span>篇文章</span>
            </span>
          </p>
        </div>
      </div>
    </section>

    <main class="flex-1 container-page pb-20">
      <div v-if="loading" class="grid gap-6 sm:grid-cols-2">
        <USkeleton v-for="i in 4" :key="i" class="h-72 rounded-2xl" />
      </div>
      <UEmpty v-else-if="!articles.length" title="该分类下暂无文章" class="py-20" />
      <div v-else class="grid gap-6 sm:grid-cols-2">
        <ArticleCard v-for="a in articles" :key="a.id" :article="a" />
      </div>

      <div v-if="total > pageSize" class="mt-10 flex justify-center">
        <UPagination :current="page" :total="total" :page-size="pageSize" @update:current="page = $event; fetchArticles()" />
      </div>
    </main>

    <SiteFooter />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Folder, FileText } from 'lucide-vue-next'
import { getArticles, getCategories, type Article, type Category } from '@/api/articles'
import SiteNavbar from '../components/SiteNavbar.vue'
import SiteFooter from '../components/SiteFooter.vue'
import ArticleCard from '../components/ArticleCard.vue'
import { UEmpty, USkeleton, UPagination, toast } from '@/ui'

const route = useRoute()

const categoryId = ref<number>(Number(route.params.id))
const category = ref<Category | null>(null)
const articles = ref<Article[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)

const fetchCategory = async () => {
  try {
    const res = await getCategories()
    const list = res.data?.data ?? []
    category.value = list.find((c) => c.id === categoryId.value) || null
  } catch {
    /* silent */
  }
}

const fetchArticles = async () => {
  loading.value = true
  try {
    const res = await getArticles({
      category_id: categoryId.value,
      page: page.value,
      page_size: pageSize.value,
    })
    const data = res.data?.data ?? { items: [], total: 0 }
    articles.value = data.items || []
    total.value = data.total || 0
  } catch {
    toast.error('获取分类文章失败')
  } finally {
    loading.value = false
  }
}

watch(
  () => route.params.id,
  (id) => {
    categoryId.value = Number(id)
    page.value = 1
    fetchCategory()
    fetchArticles()
  }
)

onMounted(() => {
  fetchCategory()
  fetchArticles()
})
</script>
