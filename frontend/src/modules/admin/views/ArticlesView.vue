<template>
  <div class="space-y-4">
    <UCard padding="md" body-class="space-y-4">
      <div class="flex flex-wrap items-center gap-3">
        <div class="flex-1 min-w-[200px]">
          <UInput
            v-model="queryParams.keyword"
            placeholder="搜索标题或内容…"
            :prefix-icon="Search"
            @keyup.enter="handleSearch"
          />
        </div>
        <USelect
          v-model="queryParams.status_filter"
          placeholder="状态"
          :options="statusOptions"
          class="w-32"
          @change="handleSearch"
        />
        <UButton variant="primary" @click="handleSearch">
          <template #icon><Search class="size-4" /></template>
          搜索
        </UButton>
        <UButton variant="ghost" @click="handleReset">
          <template #icon><RotateCcw class="size-4" /></template>
          重置
        </UButton>
        <div class="ml-auto">
          <UButton variant="primary" @click="$router.push('/admin/articles/new')">
            <template #icon><Plus class="size-4" /></template>
            新建文章
          </UButton>
        </div>
      </div>

      <div class="overflow-x-auto rounded-lg border border-[var(--border)]">
        <table class="w-full text-sm">
          <thead class="bg-[var(--bg-soft)] text-[var(--text-soft)]">
            <tr>
              <th class="px-4 py-3 text-left font-medium w-16">ID</th>
              <th class="px-4 py-3 text-left font-medium">标题</th>
              <th class="px-4 py-3 text-left font-medium w-32">分类</th>
              <th class="px-4 py-3 text-center font-medium w-24">状态</th>
              <th class="px-4 py-3 text-center font-medium w-24">阅读量</th>
              <th class="px-4 py-3 text-center font-medium w-44">发布时间</th>
              <th class="px-4 py-3 text-right font-medium w-44">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--border)] bg-[var(--surface)]">
            <tr v-if="loading">
              <td colspan="7" class="px-4 py-12 text-center">
                <USpinner :size="20" />
              </td>
            </tr>
            <tr v-else-if="articles.length === 0">
              <td colspan="7" class="px-4 py-12">
                <UEmpty description="暂无文章" />
              </td>
            </tr>
            <tr
              v-for="row in articles"
              :key="row.id"
              class="hover:bg-[var(--bg-muted)] transition-colors"
            >
              <td class="px-4 py-3 text-[var(--text-muted)]">{{ row.id }}</td>
              <td class="px-4 py-3 text-[var(--text)] font-medium">{{ row.title }}</td>
              <td class="px-4 py-3 text-[var(--text-soft)]">{{ row.category?.name || '-' }}</td>
              <td class="px-4 py-3 text-center">
                <UTag :variant="row.status === 'published' ? 'success' : (row.status === 'draft' ? 'neutral' : 'warning')">
                  {{
                    row.status === 'published'
                      ? '已发布'
                      : row.status === 'draft'
                        ? (row.is_draft_copy ? '草稿副本' : '草稿')
                        : '已下线'
                  }}
                </UTag>
              </td>
              <td class="px-4 py-3 text-center text-[var(--text-soft)]">{{ row.view_count }}</td>
              <td class="px-4 py-3 text-center text-xs text-[var(--text-muted)]">
                {{ formatDateTime(row.published_at || row.created_at) }}
              </td>
              <td class="px-4 py-3 text-right">
                <div class="inline-flex gap-1">
                  <button
                    class="text-xs px-2 py-1 rounded hover:bg-[var(--brand-soft)] text-[var(--brand)]"
                    @click="$router.push(`/admin/articles/edit/${row.id}`)"
                  >编辑</button>
                  <button
                    :class="['text-xs px-2 py-1 rounded', row.status === 'published' ? 'hover:bg-amber-50 text-amber-600' : 'hover:bg-emerald-50 text-emerald-600']"
                    @click="handleToggleStatus(row)"
                  >{{ row.status === 'published' ? '下架' : '发布' }}</button>
                  <button
                    class="text-xs px-2 py-1 rounded hover:bg-rose-50 text-rose-500"
                    @click="handleDelete(row)"
                  >删除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="flex flex-col sm:flex-row items-center justify-between gap-3">
        <p class="text-sm text-[var(--text-muted)]">共 {{ total }} 条数据</p>
        <UPagination
          v-model:current="queryParams.page"
          :page-size="queryParams.page_size"
          :total="total"
          @change="fetchArticles"
        />
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { Search, RotateCcw, Plus } from 'lucide-vue-next'
import { getAdminArticles, deleteArticle, publishArticle, unpublishArticle } from '@/api/articles'
import { formatDateTime } from '@/utils/time'
import { UCard, UInput, USelect, UButton, UTag, UEmpty, USpinner, UPagination, toast, confirmDialog } from '@/ui'

const loading = ref(false)
const articles = ref<any[]>([])
const total = ref(0)

const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '已发布', value: 'published' },
  { label: '草稿', value: 'draft' },
]

const queryParams = reactive({
  page: 1,
  page_size: 10,
  keyword: '',
  status_filter: '',
})

const fetchArticles = async () => {
  try {
    loading.value = true
    const res = await getAdminArticles(queryParams)
    articles.value = res.data?.data?.items ?? []
    total.value = res.data?.data?.total ?? 0
  } catch (e) {
    toast.error('获取文章列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  queryParams.page = 1
  fetchArticles()
}

const handleReset = () => {
  queryParams.keyword = ''
  queryParams.status_filter = ''
  handleSearch()
}

const handleToggleStatus = async (row: any) => {
  try {
    if (row.status === 'published') {
      await unpublishArticle(row.id)
      toast.success('已下架')
    } else {
      await publishArticle(row.id)
      toast.success('已发布')
    }
    fetchArticles()
  } catch {
    toast.error('操作失败')
  }
}

const handleDelete = async (row: any) => {
  const ok = await confirmDialog({
    title: '删除文章',
    message: `确定要删除「${row.title}」吗？此操作不可恢复。`,
    confirmText: '删除',
    danger: true,
  })
  if (!ok) return
  try {
    await deleteArticle(row.id)
    toast.success('删除成功')
    if (articles.value.length === 1 && queryParams.page > 1) queryParams.page--
    fetchArticles()
  } catch {
    toast.error('删除失败')
  }
}

onMounted(fetchArticles)
</script>
