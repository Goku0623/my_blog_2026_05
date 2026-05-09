<template>
  <div class="space-y-4">
    <UCard padding="md" body-class="space-y-4">
      <div class="flex flex-wrap items-center gap-3">
        <div class="flex-1 min-w-[220px]">
          <UInput
            v-model="queryParams.keyword"
            placeholder="按留言内容搜索…"
            :prefix-icon="Search"
            @keyup.enter="handleSearch"
          />
        </div>
        <UButton variant="primary" @click="handleSearch">
          <template #icon><Search class="size-4" /></template>
          搜索
        </UButton>
        <UButton variant="ghost" @click="handleReset">
          <template #icon><RotateCcw class="size-4" /></template>
          重置
        </UButton>
      </div>

      <div v-if="selectedIds.length > 0" class="flex items-center gap-2 px-3 py-2 rounded-lg bg-[var(--brand-soft)] text-[var(--brand)] text-sm">
        <CheckSquare class="size-4" />
        已选择 {{ selectedIds.length }} 条
        <div class="ml-auto flex gap-2">
          <UButton size="sm" variant="subtle" @click="handleBatchAction('approve')">公开</UButton>
          <UButton size="sm" variant="subtle" @click="handleBatchAction('hide')">隐藏</UButton>
          <UButton size="sm" variant="danger" @click="handleBatchAction('delete')">删除</UButton>
        </div>
      </div>

      <div class="overflow-x-auto rounded-lg border border-[var(--border)]">
        <table class="w-full text-sm">
          <thead class="bg-[var(--bg-soft)] text-[var(--text-soft)]">
            <tr>
              <th class="px-3 py-3 w-10 text-center">
                <input type="checkbox" :checked="allSelected" @change="toggleSelectAll" class="accent-[var(--brand)]" />
              </th>
              <th class="px-4 py-3 text-left font-medium w-16">ID</th>
              <th class="px-4 py-3 text-left font-medium w-36">昵称</th>
              <th class="px-4 py-3 text-left font-medium">内容</th>
              <th class="px-4 py-3 text-center font-medium w-24">状态</th>
              <th class="px-4 py-3 text-center font-medium w-44">时间</th>
              <th class="px-4 py-3 text-right font-medium w-44">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--border)] bg-[var(--surface)]">
            <tr v-if="loading">
              <td colspan="7" class="px-4 py-12 text-center"><USpinner :size="20" /></td>
            </tr>
            <tr v-else-if="messages.length === 0">
              <td colspan="7" class="px-4 py-12"><UEmpty description="暂无留言" /></td>
            </tr>
            <tr
              v-for="row in messages"
              :key="row.id"
              class="hover:bg-[var(--bg-muted)] transition-colors"
            >
              <td class="px-3 py-3 text-center">
                <input type="checkbox" :checked="selectedIds.includes(row.id)" @change="toggleRow(row.id)" class="accent-[var(--brand)]" />
              </td>
              <td class="px-4 py-3 text-[var(--text-muted)]">{{ row.id }}</td>
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <UAvatar :name="row.guest_name" :size="28" />
                  <span class="text-[var(--text)]">{{ row.guest_name }}</span>
                </div>
              </td>
              <td class="px-4 py-3 text-[var(--text-soft)] max-w-xl">
                <p class="line-clamp-2">{{ row.content }}</p>
              </td>
              <td class="px-4 py-3 text-center">
                <UTag :variant="statusVariant(row.status)">{{ statusLabel(row.status) }}</UTag>
              </td>
              <td class="px-4 py-3 text-center text-xs text-[var(--text-muted)]">{{ formatDateTime(row.created_at) }}</td>
              <td class="px-4 py-3 text-right">
                <div class="inline-flex gap-1">
                  <button class="text-xs px-2 py-1 rounded hover:bg-[var(--brand-soft)] text-[var(--brand)]" @click="openDetail(row)">详情</button>
                  <button
                    v-if="row.status !== 'hidden'"
                    class="text-xs px-2 py-1 rounded hover:bg-amber-50 text-amber-600"
                    @click="handleAction(row, 'hide')"
                  >隐藏</button>
                  <button
                    v-else
                    class="text-xs px-2 py-1 rounded hover:bg-emerald-50 text-emerald-600"
                    @click="handleAction(row, 'approve')"
                  >公开</button>
                  <button
                    class="text-xs px-2 py-1 rounded hover:bg-rose-50 text-rose-500"
                    @click="handleAction(row, 'delete')"
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
          @change="fetchMessages"
        />
      </div>
    </UCard>

    <UModal v-model="detailVisible" title="留言详情" width="lg">
      <div v-if="currentMessage" class="space-y-4 text-sm">
        <div class="grid grid-cols-2 gap-3 text-[var(--text-soft)]">
          <div><span class="text-[var(--text-muted)]">ID：</span>{{ currentMessage.id }}</div>
          <div><span class="text-[var(--text-muted)]">昵称：</span>{{ currentMessage.guest_name }}</div>
          <div><span class="text-[var(--text-muted)]">状态：</span><UTag :variant="statusVariant(currentMessage.status)">{{ statusLabel(currentMessage.status) }}</UTag></div>
          <div><span class="text-[var(--text-muted)]">IP：</span>{{ currentMessage.ip_address || '-' }}</div>
          <div><span class="text-[var(--text-muted)]">创建时间：</span>{{ formatDateTime(currentMessage.created_at) }}</div>
          <div><span class="text-[var(--text-muted)]">更新时间：</span>{{ currentMessage.updated_at ? formatDateTime(currentMessage.updated_at) : '-' }}</div>
        </div>
        <div>
          <p class="font-semibold mb-2 text-[var(--text)]">留言内容</p>
          <div class="rounded-lg border border-[var(--border)] bg-[var(--bg-soft)] p-3 leading-relaxed text-[var(--text)] whitespace-pre-wrap break-words">
            {{ currentMessage.content }}
          </div>
        </div>
      </div>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { Search, RotateCcw, CheckSquare } from 'lucide-vue-next'
import { formatDateTime } from '@/utils/time'
import {
  getAdminGuestbookMessages,
  guestbookMessageAction,
  type GuestbookMessage,
} from '@/api/guestbook'
import {
  UCard, UInput, UButton, UTag, UEmpty, USpinner, UPagination, UAvatar, UModal,
  toast, confirmDialog,
} from '@/ui'

const loading = ref(false)
const messages = ref<GuestbookMessage[]>([])
const total = ref(0)
const selectedIds = ref<number[]>([])

const queryParams = reactive({ page: 1, page_size: 20, keyword: '' })

const detailVisible = ref(false)
const currentMessage = ref<GuestbookMessage | null>(null)

const allSelected = computed(() =>
  messages.value.length > 0 && messages.value.every((m) => selectedIds.value.includes(m.id))
)

const fetchMessages = async () => {
  try {
    loading.value = true
    const res = await getAdminGuestbookMessages({
      page: queryParams.page,
      page_size: queryParams.page_size,
      keyword: queryParams.keyword || undefined,
    })
    messages.value = res.data?.data?.items ?? []
    total.value = res.data?.data?.total ?? 0
    selectedIds.value = []
  } catch {
    toast.error('获取留言列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  queryParams.page = 1
  fetchMessages()
}

const handleReset = () => {
  queryParams.keyword = ''
  handleSearch()
}

const statusVariant = (status: string) => {
  if (status === 'approved') return 'success' as const
  if (status === 'hidden') return 'danger' as const
  return 'warning' as const
}

const statusLabel = (status: string) => {
  if (status === 'approved') return '已发布'
  if (status === 'hidden') return '已隐藏'
  return '已删除'
}

const toggleRow = (id: number) => {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

const toggleSelectAll = () => {
  if (allSelected.value) selectedIds.value = []
  else selectedIds.value = messages.value.map((m) => m.id)
}

const handleAction = async (row: GuestbookMessage, action: 'approve' | 'hide' | 'delete') => {
  if (action === 'delete') {
    const ok = await confirmDialog({
      title: '删除留言',
      message: '确定要删除该留言吗？此操作不可恢复。',
      confirmText: '删除',
      danger: true,
    })
    if (!ok) return
  }

  try {
    await guestbookMessageAction(row.id, action)
    toast.success('操作成功')
    if (action === 'delete' && messages.value.length === 1 && queryParams.page > 1) {
      queryParams.page--
    }
    fetchMessages()
  } catch {
    toast.error('操作失败')
  }
}

const handleBatchAction = async (action: 'approve' | 'hide' | 'delete') => {
  const nameMap: Record<string, string> = {
    approve: '公开',
    hide: '隐藏',
    delete: '删除',
  }
  const ok = await confirmDialog({
    title: `批量${nameMap[action]}`,
    message: `确定要批量${nameMap[action]}所选 ${selectedIds.value.length} 条留言吗？`,
    danger: action === 'delete',
  })
  if (!ok) return

  try {
    await Promise.all(selectedIds.value.map((id) => guestbookMessageAction(id, action)))
    toast.success(`批量${nameMap[action]}成功`)
    fetchMessages()
  } catch {
    toast.error(`批量${nameMap[action]}部分失败`)
  }
}

const openDetail = (row: GuestbookMessage) => {
  currentMessage.value = row
  detailVisible.value = true
}

fetchMessages()
</script>
