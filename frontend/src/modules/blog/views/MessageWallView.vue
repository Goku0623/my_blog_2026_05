<template>
  <div class="min-h-screen flex flex-col bg-[var(--bg)]">
    <SiteNavbar />

    <!-- Hero -->
    <section class="relative overflow-hidden">
      <div aria-hidden="true" class="hero-orb size-[420px] -top-32 left-1/2 -translate-x-1/2 bg-[var(--accent)]/15"></div>

      <div class="container-page relative pt-12 sm:pt-16 pb-10">
        <div class="text-center max-w-3xl mx-auto">
          <span class="eyebrow"><MessageCircle class="size-3" /> 留言墙</span>
          <h1 class="mt-3 hero-headline text-[clamp(2rem,5vw,3.75rem)] text-[var(--text)] leading-[1.1]">
            留下你的<span class="text-gradient-brand">足迹</span>
          </h1>
          <p class="mt-4 text-base text-[var(--text-soft)]">
            有什么想对博主说的？在这里留下你的留言吧
          </p>
        </div>
      </div>
    </section>

    <!-- 留言列表 -->
    <main class="flex-1 pb-16 sm:pb-20">
      <div class="mx-auto w-[94vw] lg:w-[60vw] max-w-[980px] min-h-[52vh]">
        <div class="mb-6 flex items-end justify-between border-b border-[var(--border)] pb-4">
          <div>
            <p class="eyebrow">Messages</p>
            <h3 class="mt-2 font-display text-2xl font-bold text-[var(--text)]">
              全部留言
              <span class="ml-2 text-sm font-normal text-[var(--text-muted)] tabular-nums">({{ total }})</span>
            </h3>
          </div>
        </div>

        <div v-if="loading" class="space-y-4">
          <USkeleton v-for="i in 4" :key="i" class="h-28 rounded-2xl" />
        </div>

        <UEmpty
          v-else-if="!messages.length"
          title="还没有留言"
          description="成为第一个留言的人吧 ✨"
          class="py-20"
        />

        <div v-else class="space-y-4 sm:space-y-5">
          <div
            v-for="msg in messages"
            :key="msg.id"
            class="group relative rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 sm:p-6 md:p-7 shadow-[var(--shadow-sm)] hover:shadow-[var(--shadow-md)] hover:border-[var(--border-strong)] transition-all duration-200"
          >
            <div class="absolute top-3 right-3 size-2.5 rounded-full bg-[var(--accent)]/40" />
            <div class="flex items-start gap-4">
              <UAvatar
                :name="msg.guest_name"
                :src="msg.guest_avatar || undefined"
                :size="44"
                class="shrink-0 min-w-11 min-h-11 rounded-full overflow-hidden ring-1 ring-[var(--border)] bg-[var(--bg-soft)]"
              />
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2 mb-2">
                  <span class="text-sm font-semibold text-[var(--text)]">{{ msg.guest_name }}</span>
                  <span class="text-xs text-[var(--text-muted)]">{{ formatTime(msg.created_at) }}</span>
                </div>
                <div
                  class="message-content prose prose-sm max-w-none dark:prose-invert text-[var(--text-soft)] leading-relaxed"
                  v-html="msg.rendered_content || msg.content"
                />
              </div>
            </div>
          </div>

          <div v-if="total > pageSize" class="mt-10 flex justify-center">
            <UPagination
              v-model:current="currentPage"
              :page-size="pageSize"
              :total="total"
              @change="fetchMessages"
            />
          </div>
        </div>
      </div>
    </main>

    <!-- 留言输入区 -->
    <section class="pb-14 sm:pb-16">
      <div class="mx-auto w-[94vw] lg:w-[60vw] max-w-[980px]">
        <div class="rounded-2xl border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-sm)] overflow-hidden min-h-[40vh]">
          <div class="px-5 sm:px-7 py-4 border-b border-[var(--border)] bg-[var(--bg-soft)]/60">
            <p class="eyebrow">Write a Message</p>
            <p class="mt-2 text-sm text-[var(--text-soft)]">在下方输入你的留言，支持 Markdown 语法</p>
          </div>

          <div v-if="!guestStore.isGuest" class="flex flex-col items-center gap-3 p-8 sm:p-10 text-center">
            <div class="grid place-items-center size-12 rounded-full bg-[var(--brand-soft)]">
              <MessageCircle class="size-5 text-[var(--brand)]" />
            </div>
            <div>
              <p class="font-medium text-[var(--text)]">留下你的留言</p>
              <p class="text-xs text-[var(--text-muted)] mt-1">点击下方按钮以游客身份开始留言</p>
            </div>
            <UButton variant="primary" @click="initGuest">点击开始留言</UButton>
          </div>

          <div v-else class="p-5 sm:p-7 space-y-4">
            <div class="flex items-center gap-3">
              <UAvatar :name="guestDisplayName" :src="siteStore.config.admin_avatar || undefined" :size="40" />
              <div class="flex flex-wrap items-center gap-2 text-sm min-w-0">
                <span class="font-medium text-[var(--text)]">{{ guestDisplayName }}</span>
                <span class="text-xs text-[var(--text-muted)]">写下你想说的话…</span>
              </div>
            </div>

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
              v-model="formContent"
              type="textarea"
              :rows="5"
              :maxlength="500"
              show-count
              class="w-full"
              placeholder="支持 Markdown 语法，说点什么吧…"
            />
            <div
              v-else
              class="message-content prose prose-sm max-w-none dark:prose-invert min-h-[136px] rounded-lg border border-[var(--border-strong)] bg-[var(--bg-soft)] p-4"
              v-html="renderedPreview || '<p class=\'text-sm text-[var(--text-muted)]\'>暂无内容</p>'"
            />

            <div class="flex flex-wrap items-center justify-between gap-3 pt-1">
              <p class="text-xs text-[var(--text-muted)]">
                支持 <span class="font-mono text-[var(--brand)]">Markdown</span> · 每天限 3 条
              </p>
              <UButton
                variant="primary"
                :loading="submitting"
                :disabled="!formContent.trim()"
                @click="submitMessage"
              >
                <template #icon><Send class="size-4" /></template>
                发布留言
              </UButton>
            </div>
          </div>
        </div>
      </div>
    </section>

    <SiteFooter />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import type { AxiosError } from 'axios'
import { MessageCircle, Send } from 'lucide-vue-next'
import { getGuestbookMessages, createGuestbookMessage, type GuestbookMessage } from '@/api/guestbook'
import { useGuestStore } from '@/stores/guest'
import { useSiteStore } from '@/stores/site'
import { useAuthStore } from '@/stores/auth'
import { useMarkdown } from '@/composables/useMarkdown'
import { UAvatar, UButton, UInput, UEmpty, USkeleton, UPagination, toast } from '@/ui'
import SiteNavbar from '../components/SiteNavbar.vue'
import SiteFooter from '../components/SiteFooter.vue'

const guestStore = useGuestStore()
const siteStore = useSiteStore()
const authStore = useAuthStore()
const { render } = useMarkdown()

const tabs = [
  { id: 'edit' as const, label: '编辑' },
  { id: 'preview' as const, label: '预览' },
]
const activeTab = ref<'edit' | 'preview'>('edit')

const messages = ref<GuestbookMessage[]>([])
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)
const loading = ref(false)

const formContent = ref('')
const submitting = ref(false)
const renderedPreview = ref('')
let previewRenderTimer: number | null = null

const guestDisplayName = computed(() => {
  const adminName = authStore.adminInfo?.username?.trim()
  if (authStore.isAuthenticated && adminName) return adminName

  const token = guestStore.guestToken || ''
  const short = token.replace(/-/g, '').toUpperCase().slice(0, 6)
  return guestStore.guestName || (short ? `游客${short}` : '游客')
})

const renderPreview = () => {
  renderedPreview.value = formContent.value.trim() ? render(formContent.value) : ''
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

const formatTime = (dateStr: string) => {
  const d = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  if (hours < 24) return `${hours} 小时前`
  if (days < 7) return `${days} 天前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

const initGuest = async () => {
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

const submitMessage = async () => {
  if (!formContent.value.trim()) return
  try {
    submitting.value = true
    await createGuestbookMessage(formContent.value.trim())
    toast.success('留言发布成功')
    formContent.value = ''
    activeTab.value = 'edit'
    currentPage.value = 1
    await fetchMessages()
  } catch (error) {
    const msg = getApiErrorMessage(error, '留言失败，请稍后重试')
    toast.error(msg)
  } finally {
    submitting.value = false
  }
}

const fetchMessages = async () => {
  try {
    loading.value = true
    const res = await getGuestbookMessages({
      page: currentPage.value,
      page_size: pageSize.value,
    })
    const data = res.data?.data ?? { items: [], total: 0 }
    messages.value = data.items ?? []
    total.value = data.total ?? 0
  } catch (e) {
    console.error('获取留言失败', e)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    await guestStore.initGuest()
  } catch {
  }
  await fetchMessages()
})

watch(formContent, () => {
  schedulePreviewRender()
})

watch(activeTab, (tab) => {
  if (tab === 'preview') {
    schedulePreviewRender(true)
  }
})

onBeforeUnmount(() => {
  if (previewRenderTimer !== null) {
    window.clearTimeout(previewRenderTimer)
    previewRenderTimer = null
  }
})
</script>

<style scoped>
.message-content {
  overflow-wrap: anywhere;
  word-break: break-word;
}

.message-content :deep(pre),
.message-content :deep(code),
.message-content :deep(table),
.message-content :deep(img) {
  max-width: 100%;
}

.message-content :deep(pre) {
  overflow-x: auto;
}

.message-content :deep(table) {
  display: block;
  overflow-x: auto;
}

.message-content :deep(img) {
  height: auto;
}
</style>