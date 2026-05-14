<template>
  <div class="space-y-4">
    <UCard padding="md" body-class="space-y-4">
      <div class="flex flex-wrap items-center gap-3">
        <div class="flex-1 min-w-[200px]">
          <UInput
            v-model="queryParams.keyword"
            placeholder="按评论内容搜索…"
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
        <table class="w-full text-sm" v-memo="[loading, comments, selectedSignature, total]">
          <thead class="bg-[var(--bg-soft)] text-[var(--text-soft)]">
            <tr>
              <th class="px-3 py-3 w-10 text-center">
                <input type="checkbox" :checked="allSelected" @change="toggleSelectAll" class="accent-[var(--brand)]" />
              </th>
              <th class="px-4 py-3 text-left font-medium w-16">ID</th>
              <th class="px-4 py-3 text-left font-medium w-36">昵称</th>
              <th class="px-4 py-3 text-left font-medium">内容</th>
              <th class="px-4 py-3 text-left font-medium w-44">所属文章</th>
              <th class="px-4 py-3 text-center font-medium w-24">状态</th>
              <th class="px-4 py-3 text-center font-medium w-44">时间</th>
              <th class="px-4 py-3 text-right font-medium w-44">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-[var(--border)] bg-[var(--surface)]">
            <tr v-if="loading">
              <td colspan="8" class="px-4 py-12 text-center"><USpinner :size="20" /></td>
            </tr>
            <tr v-else-if="comments.length === 0">
              <td colspan="8" class="px-4 py-12"><UEmpty description="暂无评论" /></td>
            </tr>
            <tr
              v-for="row in comments"
              :key="row.id"
              v-memo="[row, selectedIds.includes(row.id)]"
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
              <td class="px-4 py-3 text-[var(--text-soft)] max-w-md">
                <p class="line-clamp-2">{{ row.content }}</p>
              </td>
              <td class="px-4 py-3 text-[var(--text-muted)] text-xs truncate max-w-[180px]">{{ row.article_title || '#' + row.article_id }}</td>
              <td class="px-4 py-3 text-center">
                <UTag :variant="statusVariant(row)">{{ statusLabel(row) }}</UTag>
              </td>
              <td class="px-4 py-3 text-center text-xs text-[var(--text-muted)]">{{ formatDateTime(row.created_at) }}</td>
              <td class="px-4 py-3 text-right">
                <div class="inline-flex gap-1">
                  <button class="text-xs px-2 py-1 rounded hover:bg-[var(--brand-soft)] text-[var(--brand)]" @click="openDrawer(row)">详情</button>
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
          @change="handlePageChange"
        />
      </div>
    </UCard>

    <!-- 详情侧抽屉（用 Modal 大宽度近似） -->
    <UModal v-model="drawerVisible" title="评论详情" width="lg" :backdrop-blur="false">
      <div v-if="currentComment" class="space-y-5 text-sm">
        <div class="grid grid-cols-2 gap-3 text-[var(--text-soft)]">
          <div><span class="text-[var(--text-muted)]">ID：</span>{{ currentComment.id }}</div>
          <div><span class="text-[var(--text-muted)]">所属文章：</span>{{ currentComment.article_title || '#' + currentComment.article_id }}</div>
          <div><span class="text-[var(--text-muted)]">游客昵称：</span>{{ currentComment.guest_name }}</div>
          <div><span class="text-[var(--text-muted)]">游客邮箱：</span>{{ currentComment.guest_email || '未提供' }}</div>
          <div class="col-span-2"><span class="text-[var(--text-muted)]">个人网站：</span>{{ currentComment.guest_website || '未提供' }}</div>
          <div class="col-span-2"><span class="text-[var(--text-muted)]">IP：</span>{{ currentComment.ip_address }}</div>
          <div class="col-span-2 break-all"><span class="text-[var(--text-muted)]">UA：</span>{{ currentComment.user_agent }}</div>
          <div><span class="text-[var(--text-muted)]">状态：</span>
            <UTag :variant="statusVariant(currentComment)">{{ statusLabel(currentComment) }}</UTag>
          </div>
        </div>

        <div>
          <p class="font-semibold mb-2 text-[var(--text)]">评论内容</p>
          <div class="rounded-lg border border-[var(--border)] bg-[var(--bg-soft)] p-3 leading-relaxed text-[var(--text)] whitespace-pre-wrap break-words">
            {{ currentComment.content }}
          </div>
        </div>

        <div>
          <p class="font-semibold mb-2 text-[var(--text)]">管理员回复</p>
          <UInput v-model="replyContent" type="textarea" :rows="3" placeholder="输入回复内容…" />
          <div class="mt-2 flex justify-end">
            <UButton variant="primary" :disabled="!replyContent.trim()" :loading="replying" @click="handleAdminReply">
              发送回复
            </UButton>
          </div>
        </div>

        <div v-if="currentComment.replies && currentComment.replies.length">
          <p class="font-semibold mb-2 text-[var(--text)]">回复链</p>
          <ol class="space-y-2">
            <li v-for="r in currentComment.replies" :key="r.id" class="rounded-lg border border-[var(--border)] p-3">
              <div class="text-xs text-[var(--text-muted)] mb-1">{{ formatDateTime(r.created_at) }}</div>
              <p class="text-sm"><strong>{{ r.guest_name }}</strong>：{{ r.content }}</p>
            </li>
          </ol>
        </div>
      </div>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { Search, RotateCcw, CheckSquare } from 'lucide-vue-next'
import { getAdminComments, commentAction, adminReplyComment, type Comment } from '@/api/comments'
import { formatDateTime } from '@/utils/time'
import {
  UCard, UInput, UButton, UTag, UEmpty, USpinner, UPagination, UAvatar, UModal,
  toast, confirmDialog,
} from '@/ui'

const loading = ref(false)
const comments = ref<Comment[]>([])
const total = ref(0)
const selectedIds = ref<number[]>([])

const queryParams = reactive({ page: 1, page_size: 20, keyword: '' })
let searchDebounceTimer: number | null = null
let commentsAbortController: AbortController | null = null
let commentsFetchSerial = 0

const drawerVisible = ref(false)
const currentComment = ref<Comment | null>(null)
const replyContent = ref('')
const replying = ref(false)

const allSelected = computed(() =>
  comments.value.length > 0 && comments.value.every((c) => selectedIds.value.includes(c.id))
)
const selectedSignature = computed(() => selectedIds.value.join(','))

const fetchComments = async (options?: { silent?: boolean }) => {
  const silent = options?.silent === true
  const currentSerial = ++commentsFetchSerial
  commentsAbortController?.abort()
  commentsAbortController = new AbortController()
  try {
    if (!silent) loading.value = true
    const res = await getAdminComments({
      page: queryParams.page,
      page_size: queryParams.page_size,
      keyword: queryParams.keyword || undefined,
    } as any, commentsAbortController.signal)
    if (currentSerial !== commentsFetchSerial) return
    comments.value = res.data?.data?.items ?? []
    total.value = res.data?.data?.total ?? 0
    selectedIds.value = []
  } catch (error: any) {
    if (error?.code === 'ERR_CANCELED' || error?.name === 'CanceledError') return
    toast.error('获取评论列表失败')
  } finally {
    if (currentSerial === commentsFetchSerial) loading.value = false
  }
}

const handleSearch = () => {
  queryParams.page = 1
  fetchComments()
}

const handlePageChange = () => {
  fetchComments()
}

const scheduleKeywordSearch = () => {
  if (searchDebounceTimer !== null) {
    window.clearTimeout(searchDebounceTimer)
  }
  searchDebounceTimer = window.setTimeout(() => {
    searchDebounceTimer = null
    queryParams.page = 1
    fetchComments()
  }, 240)
}

const handleReset = () => {
  queryParams.keyword = ''
  handleSearch()
}

const isApproved = (row: Comment) => row.status === 'approved'
const statusVariant = (row: Comment) => {
  if (isApproved(row)) return 'success' as const
  if (row.status === 'hidden') return 'danger' as const
  return 'warning' as const
}
const statusLabel = (row: Comment) => {
  if (isApproved(row)) return '已发布'
  if (row.status === 'hidden') return '已隐藏'
  return '已删除'
}

const toggleRow = (id: number) => {
  const idx = selectedIds.value.indexOf(id)
  if (idx >= 0) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}

const toggleSelectAll = () => {
  if (allSelected.value) selectedIds.value = []
  else selectedIds.value = comments.value.map((c) => c.id)
}

const handleAction = async (row: Comment, action: string) => {
  if (action === 'delete') {
    const ok = await confirmDialog({
      title: '删除评论',
      message: '确定要删除该评论吗？此操作不可恢复。',
      confirmText: '删除',
      danger: true,
    })
    if (!ok) return
  }
  try {
    await commentAction(row.id, action)
    toast.success('操作成功')
    if (action === 'delete' && comments.value.length === 1 && queryParams.page > 1) {
      queryParams.page--
    }
    fetchComments()
  } catch {
    toast.error('操作失败')
  }
}

const handleBatchAction = async (action: string) => {
  const nameMap: Record<string, string> = {
    approve: '公开',
    hide: '隐藏',
    delete: '删除',
  }
  const name = nameMap[action] || '操作'
  const ok = await confirmDialog({
    title: `批量${name}`,
    message: `确定要批量${name}所选 ${selectedIds.value.length} 条评论吗？`,
    danger: action === 'delete',
  })
  if (!ok) return
  try {
    await Promise.all(selectedIds.value.map((id) => commentAction(id, action)))
    toast.success(`批量${name}成功`)
    fetchComments()
  } catch {
    toast.error(`批量${name}部分失败`)
  }
}

const openDrawer = (row: Comment) => {
  currentComment.value = row
  replyContent.value = ''
  drawerVisible.value = true
}

const handleAdminReply = async () => {
  if (!currentComment.value || !replyContent.value.trim()) return
  try {
    replying.value = true
    const res = await adminReplyComment(currentComment.value.id, replyContent.value)
    toast.success('回复成功')
    replyContent.value = ''
    // 同步抽屉内数据，避免用户误以为未生效。
    const updated = res.data?.data as Comment | undefined
    if (updated) currentComment.value = updated
    await fetchComments()
  } catch {
    toast.error('回复失败')
  } finally {
    replying.value = false
  }
}

onMounted(fetchComments)

watch(() => queryParams.keyword, (next, prev) => {
  if (next === prev) return
  scheduleKeywordSearch()
})

onBeforeUnmount(() => {
  commentsAbortController?.abort()
  if (searchDebounceTimer !== null) {
    window.clearTimeout(searchDebounceTimer)
    searchDebounceTimer = null
  }
})
</script>
