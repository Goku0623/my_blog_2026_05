<template>
  <div class="space-y-4">
    <div>
      <h1 class="text-xl font-semibold text-[var(--text)]">操作日志</h1>
      <p class="text-sm text-[var(--text-muted)] mt-1">查看后台管理操作的完整审计记录</p>
    </div>

    <UCard padding="md">
      <form class="flex flex-wrap gap-3 items-end" @submit.prevent="onSearch">
        <div class="space-y-1.5">
          <label class="text-sm font-medium text-[var(--text-soft)]">操作人</label>
          <UInput v-model="filters.operator" placeholder="管理员账号" class="w-44" />
        </div>
        <div class="space-y-1.5">
          <label class="text-sm font-medium text-[var(--text-soft)]">操作类型</label>
          <USelect v-model="filters.action" :options="actionOptions" class="w-44" />
        </div>
        <div class="space-y-1.5">
          <label class="text-sm font-medium text-[var(--text-soft)]">开始日期</label>
          <UInput v-model="filters.start_date" type="date" class="w-44" />
        </div>
        <div class="space-y-1.5">
          <label class="text-sm font-medium text-[var(--text-soft)]">结束日期</label>
          <UInput v-model="filters.end_date" type="date" class="w-44" />
        </div>
        <div class="flex gap-2">
          <UButton variant="primary" type="submit">
            <template #icon>
              <Search class="size-4" />
            </template>
            查询
          </UButton>
          <UButton variant="ghost" type="button" @click="reset">刷新</UButton>
        </div>
      </form>
    </UCard>

    <UCard padding="none">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-[var(--bg-soft)] text-[var(--text-soft)]">
            <tr>
              <th class="px-4 py-2.5 text-left font-medium w-44">时间</th>
              <th class="px-4 py-2.5 text-left font-medium">操作人</th>
              <th class="px-4 py-2.5 text-left font-medium">动作</th>
              <th class="px-4 py-2.5 text-left font-medium">资源</th>
              <th class="px-4 py-2.5 text-left font-medium">IP</th>
              <th class="px-4 py-2.5 text-left font-medium">详情</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="6" class="p-12 text-center">
                <USpinner />
              </td>
            </tr>
            <tr v-else-if="!logs.length">
              <td colspan="6">
                <UEmpty title="暂无日志" class="py-12" />
              </td>
            </tr>
            <tr v-for="log in logs" :key="log.id" class="border-t border-[var(--border)] hover:bg-[var(--bg-soft)]/40">
              <td class="px-4 py-3 text-[var(--text-soft)]">{{ formatDate(log.created_at) }}</td>
              <td class="px-4 py-3 font-medium text-[var(--text)]">{{ log.operator }}</td>
              <td class="px-4 py-3">
                <UTag :variant="actionVariant(log.action)">{{ log.action }}</UTag>
              </td>
              <td class="px-4 py-3 text-[var(--text-soft)]">
                {{ log.target_type || '-' }}<span v-if="log.target_id"> #{{ log.target_id }}</span>
              </td>
              <td class="px-4 py-3 font-mono text-xs text-[var(--text-muted)]">{{ log.ip_address }}</td>
              <td class="px-4 py-3 max-w-md truncate text-[var(--text-soft)]" :title="log.detail || ''">
                {{ log.detail || '-' }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="total > pageSize" class="p-4 border-t border-[var(--border)] flex justify-end">
        <UPagination :current="page" :total="total" :page-size="pageSize"
          @update:current="page = $event; fetchLogs()" />
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { Search } from 'lucide-vue-next'
import { getOperationLogs, type OperationLog } from '@/api/system'
import { UCard, UInput, USelect, UButton, UTag, UEmpty, USpinner, UPagination, toast } from '@/ui'

const logs = ref<OperationLog[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

const filters = reactive({
  operator: '',
  action: '',
  start_date: '',
  end_date: '',
})

const actionOptions = [
  { label: '全部', value: '' },
  { label: '创建文章', value: 'article_create' },
  { label: '更新文章', value: 'article_update' },
  { label: '删除文章', value: 'article_delete' },
  { label: '发布文章', value: 'article_publish' },
  { label: '下架文章', value: 'article_unpublish' },
  { label: '评论回复', value: 'comment_reply' },
]

const actionVariant = (a: string) => {
  const k = a?.toUpperCase()
  if (k.includes('DELETE')) return 'danger'
  if (k.includes('CREATE') || k.includes('PUBLISH')) return 'success'
  if (k.includes('UPDATE') || k.includes('UNPUBLISH')) return 'warning'
  if (k === 'LOGIN' || k === 'LOGOUT') return 'info'
  return 'neutral'
}

const formatDate = (s: string) => {
  if (!s) return '-'
  const d = new Date(s)
  return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

const fetchLogs = async () => {
  loading.value = true
  try {
    const res = await getOperationLogs({
      page: page.value,
      page_size: pageSize.value,
      operator: filters.operator || undefined,
      action: filters.action || undefined,
      start_date: filters.start_date || undefined,
      end_date: filters.end_date || undefined,
    })
    const data = res.data?.data ?? { items: [], total: 0 }
    logs.value = data.items || []
    total.value = data.total || 0
  } catch {
    toast.error('获取日志失败')
  } finally {
    loading.value = false
  }
}

const onSearch = () => { page.value = 1; fetchLogs() }
const reset = () => {
  filters.operator = ''
  filters.action = ''
  filters.start_date = ''
  filters.end_date = ''
  onSearch()
}

onMounted(fetchLogs)
</script>
