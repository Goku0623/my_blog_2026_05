<template>
  <section class="space-y-6">
    <!-- 标题 -->
    <header class="flex items-end justify-between border-b border-[var(--border)] pb-4">
      <div>
        <p class="eyebrow">Discussion</p>
        <h3 class="mt-2 font-display text-2xl font-bold text-[var(--text)]">
          评论
          <span class="ml-2 text-sm font-normal text-[var(--text-muted)] tabular-nums">({{ total }})</span>
        </h3>
      </div>
      <p v-if="aiPolling" class="text-xs text-[var(--brand)] flex items-center gap-1.5 animate-pulse-soft">
        <span class="size-1.5 rounded-full bg-[var(--brand)]"></span>
        AI 助手正在回复...
      </p>
    </header>

    <!-- 输入区 -->
    <div class="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-sm)] overflow-hidden">
      <div v-if="!guestStore.isGuest" class="flex flex-col items-center gap-3 p-8 text-center">
        <div class="grid place-items-center size-12 rounded-full bg-[var(--brand-soft)]">
          <MessageCircle class="size-5 text-[var(--brand)]" />
        </div>
        <div>
          <p class="font-medium text-[var(--text)]">加入讨论</p>
          <p class="text-xs text-[var(--text-muted)] mt-1">点击下方按钮以游客身份开启评论</p>
        </div>
        <UButton variant="primary" @click="initGuestSession">点击开启评论</UButton>
      </div>

      <div v-else class="flex gap-4 p-5 sm:p-6">
        <UAvatar :name="currentDisplayName" :src="currentAvatar" :size="40" />

        <div class="flex-1 min-w-0 space-y-3">
          <div class="flex items-center gap-2 text-sm">
            <span class="font-medium text-[var(--text)]">{{ currentDisplayName }}</span>
            <span class="text-xs text-[var(--text-muted)]">说点什么…</span>
          </div>

          <!-- 回复指示 -->
          <div
            v-if="replyingTo"
            class="flex items-center justify-between rounded-lg bg-[var(--brand-soft)] px-3 py-2 text-sm text-[var(--brand)]"
          >
            <span class="inline-flex items-center gap-1.5">
              <Reply class="size-3.5" />
              正在回复 <strong class="mx-1">{{ replyingTo.guest_name }}</strong>
            </span>
            <button class="text-xs hover:underline" @click="cancelReply">取消</button>
          </div>

          <!-- Tabs -->
          <div class="flex gap-1 border-b border-[var(--border)]">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              :class="[
                'px-3 py-2 text-sm border-b-2 transition-colors -mb-px',
                activeTab === tab.id
                  ? 'border-[var(--brand)] text-[var(--brand)] font-medium'
                  : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text)]',
              ]"
              @click="activeTab = tab.id"
            >{{ tab.label }}</button>
          </div>

          <UInput
            v-if="activeTab === 'edit'"
            v-model="commentForm.content"
            type="textarea"
            :rows="4"
            :maxlength="500"
            show-count
            placeholder="支持 Markdown 语法，说点什么吧…"
          />
          <div
            v-else
            class="prose prose-sm max-w-none dark:prose-invert min-h-[112px] rounded-lg border border-[var(--border-strong)] bg-[var(--bg-soft)] p-3"
            v-html="renderedPreview || '<p class=\'text-sm text-[var(--text-muted)]\'>暂无内容</p>'"
          />

          <div class="flex items-center justify-between pt-1">
            <p class="text-xs text-[var(--text-muted)]">
              支持 <span class="font-mono text-[var(--brand)]">Markdown</span>
            </p>
            <UButton
              variant="primary"
              :loading="submitting"
              :disabled="!commentForm.content.trim()"
              @click="submitComment"
            >
              <template #icon><Send class="size-4" /></template>
              发布评论
            </UButton>
          </div>
        </div>
      </div>
    </div>

    <!-- 评论列表 -->
    <div v-if="loading" class="space-y-3">
      <USkeleton v-for="i in 3" :key="i" height="100px" class="rounded-2xl" />
    </div>

    <div
      v-else-if="comments.length > 0"
      class="rounded-2xl border border-[var(--border)] bg-[var(--surface)] divide-y divide-[var(--border)]"
    >
      <CommentItem
        v-for="comment in comments"
        :key="comment.id"
        :comment="comment"
        @reply="handleReply"
      />

      <div v-if="total > pageSize" class="p-4 sm:p-5">
        <UPagination
          v-model:current="currentPage"
          :page-size="pageSize"
          :total="total"
          @change="handlePageChange"
        />
      </div>
    </div>

    <UEmpty
      v-else
      title="还没有评论"
      description="快来抢沙发吧 ✨"
      class="py-12 rounded-2xl border border-dashed border-[var(--border)] bg-[var(--bg-soft)]/50"
    />
  </section>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import type { AxiosError } from 'axios'
import { useGuestStore } from '@/stores/guest'
import { useAuthStore } from '@/stores/auth'
import { useSiteStore } from '@/stores/site'
import { getComments, createComment, type Comment } from '@/api/comments'
import { useMarkdown } from '@/composables/useMarkdown'
import { Send, Reply, MessageCircle } from 'lucide-vue-next'
import { UAvatar, UButton, UInput, UPagination, UEmpty, USkeleton, toast } from '@/ui'
import CommentItem from './CommentItem.vue'

const props = defineProps<{ articleId: number }>()

const guestStore = useGuestStore()
const authStore = useAuthStore()
const siteStore = useSiteStore()
const { render } = useMarkdown()

const tabs: { id: 'edit' | 'preview'; label: string }[] = [
  { id: 'edit', label: '编辑' },
  { id: 'preview', label: '预览' },
]
const activeTab = ref<'edit' | 'preview'>('edit')

const comments = ref<Comment[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

const submitting = ref(false)
const replyingTo = ref<Comment | null>(null)
const commentForm = reactive({ content: '' })
const aiPolling = ref(false)
let aiPollingTimer: ReturnType<typeof setInterval> | null = null
let aiPollingAttempts = 0
let aiPollingRequestInFlight = false
const AI_POLL_INTERVAL_MS = 2000
const AI_POLL_MAX_ATTEMPTS = 30
let previewRenderTimer: number | null = null

const renderedPreview = ref('')
const currentDisplayName = computed(() => {
  const adminName = authStore.adminInfo?.username?.trim()
  if (authStore.isAuthenticated && adminName) return adminName
  return guestStore.guestName || '游客'
})

const currentAvatar = computed(() => {
  if (authStore.isAuthenticated) {
    return siteStore.config.admin_avatar || undefined
  }
  return undefined
})

const fetchComments = async (silent = false) => {
  try {
    if (!silent) loading.value = true
    const res = await getComments({
      article_id: props.articleId,
      page: currentPage.value,
      page_size: pageSize.value,
    })
    const data = res.data?.data ?? { items: [], total: 0 }
    comments.value = data.items ?? []
    total.value = data.total ?? 0
  } catch (e) {
    console.warn('获取评论失败', e)
  } finally {
    if (!silent) loading.value = false
  }
}

const clearAiPolling = () => {
  if (aiPollingTimer) {
    clearInterval(aiPollingTimer)
    aiPollingTimer = null
  }
  aiPollingAttempts = 0
  aiPollingRequestInFlight = false
  aiPolling.value = false
}

const hasAiReply = (targetCommentId: number) => {
  const target = comments.value.find((item) => item.id === targetCommentId)
  if (!target) return false
  return (target.replies ?? []).some((reply) => {
    const token = reply.guest?.guest_token?.toLowerCase()
    const name = reply.guest_name || ''
    return token === 'ai-assistant' || name.includes('AI助手') || name.includes('AI助手Bot')
  })
}

const pollAiReply = async (targetCommentId: number) => {
  if (aiPollingRequestInFlight) return
  aiPollingRequestInFlight = true

  try {
    aiPollingAttempts += 1
    await fetchComments(true)

    if (hasAiReply(targetCommentId)) {
      clearAiPolling()
      toast.success('AI 助手已回复，评论区已自动刷新')
      return
    }

    if (aiPollingAttempts >= AI_POLL_MAX_ATTEMPTS) {
      clearAiPolling()
      toast.info('AI 回复仍在生成中，可稍后手动刷新查看')
    }
  } finally {
    aiPollingRequestInFlight = false
  }
}

const startAiPolling = (targetCommentId: number) => {
  clearAiPolling()
  aiPolling.value = true
  toast.info('AI 助手正在生成回复，完成后会自动刷新')
  aiPollingTimer = setInterval(() => {
    void pollAiReply(targetCommentId)
  }, AI_POLL_INTERVAL_MS)
}

const initGuestSession = async () => {
  try {
    await guestStore.initGuest()
  } catch {
    toast.error('初始化游客身份失败，请稍后重试')
  }
}

const getApiErrorMessage = (error: unknown, fallback: string) => {
  const axiosError = error as AxiosError<{ message?: string; detail?: string }>
  return axiosError.response?.data?.message
    || axiosError.response?.data?.detail
    || fallback
}

const submitComment = async () => {
  if (!commentForm.content.trim()) return
  try {
    submitting.value = true
    const isTopLevelComment = !replyingTo.value
    const response = await createComment({
      article_id: props.articleId,
      content: commentForm.content,
      parent_id: replyingTo.value ? replyingTo.value.id : undefined,
    })
    const createdCommentId = response.data?.data?.id
    toast.success('评论发布成功')
    commentForm.content = ''
    cancelReply()
    activeTab.value = 'edit'
    await fetchComments()

    if (isTopLevelComment && typeof createdCommentId === 'number' && siteStore.config.ai_enabled) {
      startAiPolling(createdCommentId)
    }
  } catch (error) {
    const errorMessage = getApiErrorMessage(error, '评论内容不能包含违禁词，或请稍后重试')
    toast.error(errorMessage)
  } finally {
    submitting.value = false
  }
}

const handleReply = (comment: Comment) => {
  if (!guestStore.isGuest) {
    initGuestSession()
    return
  }
  replyingTo.value = comment.parent_id ? { ...comment, id: comment.parent_id } : comment
  commentForm.content = `@${comment.guest_name} ` + commentForm.content
  document.querySelector('section')?.scrollIntoView({ behavior: 'smooth' })
}

const cancelReply = () => {
  replyingTo.value = null
  commentForm.content = commentForm.content.replace(/^@\S+\s/, '')
}

const handlePageChange = () => fetchComments()

const renderPreview = () => {
  renderedPreview.value = commentForm.content.trim() ? render(commentForm.content) : ''
}

const schedulePreviewRender = (immediate = false) => {
  if (previewRenderTimer !== null) {
    window.clearTimeout(previewRenderTimer)
    previewRenderTimer = null
  }
  if (activeTab.value !== 'preview') return
  if (immediate) {
    renderPreview()
    return
  }
  previewRenderTimer = window.setTimeout(() => {
    previewRenderTimer = null
    renderPreview()
  }, 120)
}

const handleAdminProfileUpdated = () => {
  void fetchComments(true)
}

const handleStorage = (e: StorageEvent) => {
  if (e.key === 'admin_profile_updated_at' && e.newValue) {
    void fetchComments(true)
  }
}

onMounted(async () => {
  try {
    await guestStore.initGuest()
  } catch {
  }
  await fetchComments()
  window.addEventListener('admin-profile-updated', handleAdminProfileUpdated)
  window.addEventListener('storage', handleStorage)
})

watch(() => commentForm.content, () => {
  schedulePreviewRender()
})

watch(activeTab, (tab) => {
  if (tab === 'preview') {
    schedulePreviewRender(true)
  }
})

onBeforeUnmount(() => {
  clearAiPolling()
  if (previewRenderTimer !== null) {
    window.clearTimeout(previewRenderTimer)
    previewRenderTimer = null
  }
  window.removeEventListener('admin-profile-updated', handleAdminProfileUpdated)
  window.removeEventListener('storage', handleStorage)
})
</script>
